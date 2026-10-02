"""POST /cases/{caseId}/decision. Owner: Kaylin.

Stub: checks the role and the move, returns the sample Case with the new status.
Replace the sample with db.get_case and db.update_case, and write an audit row.
"""

from datetime import datetime, timezone

from common import case_state
from common.http import ApiError, api_handler, parse_body, path_param, require, respond
from common.roles import require_role
from common.samples import sample_case
from common.views import case_for_role


@api_handler
def handler(event, context):
    role = require_role(event, "fraud")
    case_id = path_param(event, "caseId")
    body = parse_body(event)
    require(body, "action")
    to_status = case_state.ACTION_TO_STATUS.get(body["action"])
    if not to_status:
        raise ApiError(400, "bad_request", "action must be release, extend, or escalate.")

    case = sample_case()  # TODO(Kaylin): db.get_case(case_id), 404 if None
    case["caseId"] = case_id
    if not case_state.can_move(case["status"], to_status, role):
        raise ApiError(409, "invalid_move", f"Cannot move a {case['status']} case to {to_status}.")

    case["status"] = to_status
    case["decision"] = {
        "action": body["action"],
        "by": role,
        "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "note": body.get("note", ""),
    }
    if to_status == case_state.RELEASED:
        case["holdEndsAt"] = None
    return respond(case_for_role(case, role))
