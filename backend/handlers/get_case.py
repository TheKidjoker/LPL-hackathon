"""GET /cases/{caseId}. Owner: Kaylin.

404 when the Case does not exist. The fraud role also gets the audit trail.
"""

from common import audit, db
from common.http import ApiError, api_handler, path_param, respond
from common.roles import get_role
from common.views import case_for_role


@api_handler
def handler(event, context):
    role = get_role(event)
    case_id = path_param(event, "caseId")

    case = db.get_case(case_id)
    if case is None:
        raise ApiError(404, "not_found", f"No case {case_id}.")
    if role == "fraud":
        case["audit"] = audit.list_audit(case_id)
    return respond(case_for_role(case, role))
