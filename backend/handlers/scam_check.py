"""POST /scam-check. Owner: Thomas.

A client asks Juno whether someone who contacted them is a scammer, before any money moves.
Each check is saved to the account's contactLog (one entry per checkId, updated as the chat
goes on), so the advisor and fraud team see it, and Juno's risk scoring sees it if the client
later asks to withdraw. Never returns an AI error: check_contact falls back to fixed advice.
"""

from datetime import datetime, timezone

from common import db
from common.http import ApiError, api_handler, parse_body, require, respond
from common.roles import require_role
from fraud_ai import check_contact
from fraud_ai.contact_check import CHANNELS
from handlers.assistant import validate_messages

MAX_ID = 64
VERDICT_LABELS = {
    "likely_scam": "likely a scam",
    "suspicious": "suspicious",
    "looks_safe": "looks safe",
    "need_more": "needs more detail",
}


def log_entry(check_id, account, channel, messages, result):
    first = messages[0]["text"]
    quote = first if len(first) <= 160 else first[:157].rstrip() + "..."
    pattern = f" ({result['scamType']})" if result.get("scamType") else ""
    turns = sum(1 for m in messages if m["role"] == "user")
    return {
        "id": check_id,
        "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "channel": "juno",
        "party": "client",
        "who": account.get("clientName"),
        "verdict": result["verdict"],
        "summary": (
            f"Asked Juno whether {CHANNELS.get(channel, 'a contact')} was a scam: \"{quote}\" "
            f"Juno said {VERDICT_LABELS[result['verdict']]}{pattern}"
            + (f" after {turns} messages." if turns > 1 else ".")
        ),
    }


@api_handler
def handler(event, context):
    require_role(event, "client")
    body = parse_body(event)
    require(body, "accountId", "checkId")
    channel = body.get("channel") or "phone"
    if channel not in CHANNELS:
        raise ApiError(400, "bad_request", f"channel must be one of: {', '.join(CHANNELS)}.")
    check_id = str(body["checkId"])
    if len(check_id) > MAX_ID:
        raise ApiError(400, "bad_request", f"checkId must be at most {MAX_ID} characters.")
    messages = validate_messages(body)

    account = db.get_account(body["accountId"])
    if account is None:
        raise ApiError(404, "not_found", f"No account {body['accountId']}.")

    # Only what helps spot impersonation: a caller claiming to be "your advisor" with another name.
    client = {
        "firstName": (account.get("clientName") or "").split(" ")[0],
        "clientAge": account.get("clientAge"),
        "advisorName": (account.get("advisor") or {}).get("name"),
    }
    result = check_contact(client, channel, messages)
    db.save_contact_log_entry(account["accountId"], log_entry(check_id, account, channel, messages, result))
    return respond(result)
