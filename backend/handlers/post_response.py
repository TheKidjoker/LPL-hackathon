"""POST /cases/{caseId}/responses. Owner: Krish.

Stub: validates the request and returns the sample Case with the response added.
Replace with db.get_case, append the Response, db.update_case, audit.write_audit.
For kind "chat", call fraud_ai.scam_check_chat(case, messages) and store
chatReply and done on the Response.
"""

import uuid
from datetime import datetime, timezone

from common.http import ApiError, api_handler, parse_body, path_param, require, respond
from common.roles import require_role
from common.samples import sample_case
from common.views import case_for_role

KINDS = {
    "client": {"confirm", "deny", "emergency_contact", "chat"},
    "advisor": {"note"},
}


@api_handler
def handler(event, context):
    role = require_role(event, "client", "advisor")
    case_id = path_param(event, "caseId")
    body = parse_body(event)
    require(body, "kind", "text")
    if body["kind"] not in KINDS[role]:
        raise ApiError(400, "bad_request", f"kind must be one of: {', '.join(sorted(KINDS[role]))}.")

    response = {
        "responseId": f"resp-{uuid.uuid4().hex[:8]}",
        "role": role,
        "kind": body["kind"],
        "text": body["text"],
        "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    case = sample_case()  # TODO(Krish): db.get_case(case_id), 404 if None
    case["caseId"] = case_id
    case["responses"].append(response)
    return respond(case_for_role(case, role))
