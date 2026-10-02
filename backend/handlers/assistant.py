"""POST /cases/{caseId}/assistant. Owner: Thomas.

Advisors and the fraud team ask Claude questions about one case. Claude sees only what that
role may see: the advisor never gets doNotNotify or the audit trail. Every question writes an
ASSISTANT_QUESTION audit row, so each AI consultation is on the record.
"""

import logging

from common import audit, db
from common.http import ApiError, api_handler, parse_body, path_param, respond
from common.roles import require_role
from common.views import case_for_role
from fraud_ai.assistant import ask
from handlers.case_context import contacts_of

logger = logging.getLogger()

MAX_MESSAGES = 20
MAX_TEXT = 2000


def validate_messages(body):
    messages = body.get("messages")
    if not isinstance(messages, list) or not messages:
        raise ApiError(400, "bad_request", "messages must be a non-empty list.")
    if len(messages) > MAX_MESSAGES:
        raise ApiError(400, "bad_request", f"At most {MAX_MESSAGES} messages.")
    clean = []
    for m in messages:
        if not isinstance(m, dict) or m.get("role") not in ("user", "assistant"):
            raise ApiError(400, "bad_request", "Each message needs role user or assistant.")
        text = m.get("text")
        if not isinstance(text, str) or not text.strip() or len(text) > MAX_TEXT:
            raise ApiError(400, "bad_request", f"Each message needs text of 1 to {MAX_TEXT} characters.")
        clean.append({"role": m["role"], "text": text.strip()})
    if clean[-1]["role"] != "user":
        raise ApiError(400, "bad_request", "The last message must be from the user.")
    return clean


def account_summary(account):
    # No account numbers or addresses: only what helps answer questions about the risk.
    return {
        "clientName": account.get("clientName"),
        "clientAge": account.get("clientAge"),
        "accountOpened": account.get("accountOpened"),
        "balance": account.get("balance"),
        "hasAdvisor": bool(account.get("advisor")),
        "knownPayees": [
            {"name": p.get("name"), "type": p.get("type"), "addedAt": p.get("addedAt")}
            for p in account.get("knownPayees") or []
        ],
        "contacts": [{"name": c["name"], "relationship": c["relationship"]} for c in contacts_of(account)],
        "firmContactLog": account.get("contactLog") or [],
        "advisorCrmNotes": account.get("advisorNotes") or [],
    }


def history_summary(history):
    return [
        {
            "timestamp": t.get("timestamp"),
            "type": t.get("type"),
            "amount": t.get("amount"),
            "payee": (t.get("payee") or {}).get("name"),
            "payeeType": (t.get("payee") or {}).get("type"),
        }
        for t in history or []
    ]


def build_context(case, role):
    account = db.get_account(case["accountId"]) or {}
    context = {
        "case": case_for_role(case, role),
        "account": account_summary(account),
        "history90Days": history_summary(db.get_history(case["accountId"])),
    }
    if role == "fraud":
        context["case"]["audit"] = audit.list_audit(case["caseId"])
    return context


@api_handler
def handler(event, context):
    role = require_role(event, "advisor", "fraud")
    case_id = path_param(event, "caseId")
    messages = validate_messages(parse_body(event))

    case = db.get_case(case_id)
    if case is None:
        raise ApiError(404, "not_found", f"No case {case_id}.")

    audit.write_audit(case_id, role, "ASSISTANT_QUESTION", messages[-1]["text"][:200])
    try:
        answer = ask(role, build_context(case, role), messages)
    except Exception:
        logger.exception("Assistant call failed")
        raise ApiError(502, "ai_unavailable", "The assistant is unavailable right now. Try again in a moment.")
    return respond(answer)
