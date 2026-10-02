"""GET /cases. Owner: Kaylin.

Stub: returns the sample Case as a summary. Replace with db.list_cases_by_status,
sorted HELD first, then newest first.
"""

from common.http import api_handler, respond
from common.roles import require_role
from common.samples import sample_case
from common.views import case_summary


@api_handler
def handler(event, context):
    require_role(event, "advisor", "fraud")
    status = (event.get("queryStringParameters") or {}).get("status")

    cases = [sample_case()]  # TODO(Kaylin): db.list_cases_by_status(status)
    if status:
        cases = [c for c in cases if c["status"] == status]
    return respond({"cases": [case_summary(c) for c in cases]})
