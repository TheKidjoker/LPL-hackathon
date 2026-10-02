"""GET /cases/{caseId}. Owner: Krish.

Stub: returns the sample Case for any id. Replace with db.get_case (404 when None)
and, for the fraud role, audit.list_audit for the audit field.
"""

from common.http import api_handler, path_param, respond
from common.roles import get_role
from common.samples import sample_case
from common.views import case_for_role


@api_handler
def handler(event, context):
    role = get_role(event)
    case_id = path_param(event, "caseId")

    case = sample_case()  # TODO(Krish): db.get_case(case_id), 404 if None
    case["caseId"] = case_id
    return respond(case_for_role(case, role))
