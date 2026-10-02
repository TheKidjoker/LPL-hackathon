"""POST /withdrawals. Owner: Kaylin.

1. Load the account (404 if missing) and its 90-day history
2. Build the Transaction from the request
3. Save the Case as HELD with the fallback risk before calling Claude. Scoring takes about
   10 seconds, so if the Lambda times out the withdrawal is still held for manual review
4. score_withdrawal. On any exception, keep the fallback risk (docs/api.md)
5. HELD if the score is 70 or higher or unknown, else RELEASED. holdEndsAt is 10 business days out
6. Alert everyone except doNotNotify when HELD, then save and audit the final status
"""

import logging
import uuid
from datetime import datetime, timezone

from common import audit, case_state, db
from common.http import ApiError, api_handler, parse_body, require, respond
from common.roles import require_role
from common.views import case_for_role
from fraud_ai import score_withdrawal
from fraud_ai.signals import compute_signals
from notify import notify_held

logger = logging.getLogger()

FALLBACK_MEMO = "Automated review unavailable. Held for manual review."
PAYEE_TYPES = ("bank", "crypto_exchange", "brokerage", "individual")
CHANNELS = ("web", "phone", "branch")


def fallback_risk(signals):
    return {"score": None, "level": "unknown", "signals": list(signals), "memo": FALLBACK_MEMO, "doNotNotify": []}


def is_hold(risk):
    score = risk.get("score")
    return score is None or risk.get("level") == "unknown" or score >= case_state.HOLD_THRESHOLD


def build_transaction(body, account, now):
    payee = body["payee"]
    if not isinstance(payee, dict) or not payee.get("name"):
        raise ApiError(400, "bad_request", "payee must be an object with a name.")
    if payee.get("type") not in PAYEE_TYPES:
        raise ApiError(400, "bad_request", f"payee.type must be one of: {', '.join(PAYEE_TYPES)}.")
    channel = body.get("channel") or "web"
    if channel not in CHANNELS:
        raise ApiError(400, "bad_request", f"channel must be one of: {', '.join(CHANNELS)}.")

    known = next((p for p in account.get("knownPayees") or [] if p["name"].lower() == payee["name"].lower()), None)
    return {
        "transactionId": f"txn-{uuid.uuid4().hex[:8]}",
        "accountId": account["accountId"],
        "timestamp": now,
        "type": "withdrawal",
        "amount": body["amount"],
        "payee": {
            "payeeId": known["payeeId"] if known else f"pay-{uuid.uuid4().hex[:8]}",
            "name": payee["name"],
            "type": payee["type"],
            "addedAt": payee.get("addedAt") or (known or {}).get("addedAt") or now,
        },
        "channel": channel,
        "clientNote": body.get("clientNote") or "",
    }


def score(account, transaction, history):
    try:
        return score_withdrawal(account, transaction, history)
    except Exception:
        logger.exception("score_withdrawal failed; holding for manual review")
        try:
            signals = compute_signals(account, transaction, history)
        except Exception:
            signals = []
        return fallback_risk(signals)


@api_handler
def handler(event, context):
    require_role(event, "client")
    body = parse_body(event)
    require(body, "accountId", "amount", "payee")
    if isinstance(body["amount"], bool) or not isinstance(body["amount"], (int, float)) or body["amount"] <= 0:
        raise ApiError(400, "bad_request", "amount must be a positive number.")

    account = db.get_account(body["accountId"])
    if account is None:
        raise ApiError(404, "not_found", f"No account {body['accountId']}.")
    history = db.get_history(account["accountId"])

    now_dt = datetime.now(timezone.utc)
    now = now_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    transaction = build_transaction(body, account, now)
    hold_ends = case_state.hold_end_date(now_dt.date())
    case = {
        "caseId": f"case-{uuid.uuid4().hex[:8]}",
        "accountId": account["accountId"],
        "clientName": account["clientName"],
        "createdAt": now,
        "status": case_state.HELD,
        "transaction": transaction,
        "risk": fallback_risk([]),
        "holdEndsAt": hold_ends,
        "notified": [],
        "responses": [],
        "decision": None,
    }
    db.put_case(case)
    audit.write_audit(case["caseId"], "system", "RECEIVED", "Held while automated review runs")

    risk = score(account, transaction, history)
    held = is_hold(risk)
    case["risk"] = risk
    case["status"] = case_state.HELD if held else case_state.RELEASED
    case["holdEndsAt"] = hold_ends if held else None
    case["notified"] = notify_held(case, account) if held else []

    db.update_case(case["caseId"], {k: case[k] for k in ("risk", "status", "holdEndsAt", "notified")})
    shown = "unavailable" if risk.get("score") is None else risk["score"]
    audit.write_audit(case["caseId"], "system", case["status"], f"Risk score {shown}")
    return respond(case_for_role(case, "client"), 201)
