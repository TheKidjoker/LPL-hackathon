"""GET /cases. Owner: Kaylin.

Active holds first (HELD, then EXTENDED, ESCALATED, RELEASED), newest first within each status.
"""

from common import case_state, db
from common.http import api_handler, respond
from common.roles import require_role
from common.views import case_summary

STATUS_ORDER = [case_state.HELD, case_state.EXTENDED, case_state.ESCALATED, case_state.RELEASED]


def _status_rank(case):
    status = case.get("status")
    return STATUS_ORDER.index(status) if status in STATUS_ORDER else len(STATUS_ORDER)


@api_handler
def handler(event, context):
    require_role(event, "advisor", "fraud")
    status = (event.get("queryStringParameters") or {}).get("status")

    cases = db.list_cases_by_status(status)
    cases.sort(key=lambda c: c.get("createdAt") or "", reverse=True)
    cases.sort(key=_status_rank)  # stable, so newest-first holds within each status
    return respond({"cases": [case_summary(c) for c in cases]})
