"""POST /cases/{caseId}/responses. Owner: Kaylin.

Clients confirm, deny, name an emergency contact, or answer the scam-check chat.
Advisors add notes. Nobody's response changes the status: only the fraud team decides.

For kind "chat", the conversation so far is rebuilt from earlier chat responses and passed to
scam_check_chat. Claude's answer is stored on the Response as chatReply and done. When the chat
finishes, its risk score is added to the Case's risk signals, which the client never sees.
"""

import uuid
from datetime import datetime, timezone

from common import audit, db
from common.http import ApiError, api_handler, parse_body, path_param, require, respond
from common.roles import require_role
from common.views import case_for_role
from fraud_ai import scam_check_chat

KINDS = {
    "client": {"confirm", "deny", "emergency_contact", "chat"},
    "advisor": {"note"},
}
MAX_TEXT = 2000
# The frontend shows this question before the client's first chat answer.
CHAT_OPENER = "Did someone contact you first?"


def chat_messages(case, new_text):
    """The scam-check conversation as scam_check_chat expects it, ending with the client's new answer."""
    messages = [{"role": "assistant", "text": CHAT_OPENER}]
    for r in case.get("responses") or []:
        if r.get("kind") == "chat":
            messages.append({"role": "client", "text": r["text"]})
            if r.get("chatReply"):
                messages.append({"role": "assistant", "text": r["chatReply"]})
    messages.append({"role": "client", "text": new_text})
    return messages


def chat_finished(case):
    chats = [r for r in case.get("responses") or [] if r.get("kind") == "chat"]
    return bool(chats) and bool(chats[-1].get("done"))


@api_handler
def handler(event, context):
    role = require_role(event, "client", "advisor")
    case_id = path_param(event, "caseId")
    body = parse_body(event)
    require(body, "kind", "text")
    kind = body["kind"]
    if kind not in KINDS[role]:
        raise ApiError(400, "bad_request", f"kind must be one of: {', '.join(sorted(KINDS[role]))}.")
    if not isinstance(body["text"], str) or len(body["text"]) > MAX_TEXT:
        raise ApiError(400, "bad_request", f"text must be a string of at most {MAX_TEXT} characters.")
    text = body["text"].strip()

    case = db.get_case(case_id)
    if case is None:
        raise ApiError(404, "not_found", f"No case {case_id}.")

    response = {
        "responseId": f"resp-{uuid.uuid4().hex[:8]}",
        "role": role,
        "kind": kind,
        "text": text,
        "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    changes = {}
    if kind == "chat":
        if chat_finished(case):
            raise ApiError(409, "invalid_move", "The scam check is already finished.")
        result = scam_check_chat(case, chat_messages(case, text))
        response["chatReply"] = result["reply"]
        response["done"] = bool(result["done"])
        if response["done"] and result.get("riskUpdate") is not None:
            risk = dict(case.get("risk") or {})
            risk["signals"] = list(risk.get("signals") or []) + [
                {"name": "scam_check_chat", "detail": f"Scam-check chat rated this {result['riskUpdate']}/100 likely a scam"}
            ]
            changes["risk"] = risk

    case = db.append_response(case_id, response, changes)
    if case is None:
        raise ApiError(404, "not_found", f"No case {case_id}.")
    audit.write_audit(case_id, role, kind.upper(), text[:200])
    if changes.get("risk"):
        audit.write_audit(case_id, "system", "SCAM_CHECK_DONE", changes["risk"]["signals"][-1]["detail"])
    return respond(case_for_role(case, role))
