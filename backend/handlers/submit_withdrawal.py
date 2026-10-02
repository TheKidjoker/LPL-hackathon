"""POST /withdrawals. Owner: Krish.

Stub: validates the request and returns the sample Case. Replace with:
1. db.get_account(accountId) and db.get_history(accountId), 404 if no account
2. Build the Transaction from the request
3. fraud_ai.score_withdrawal(account, transaction, history). On any exception,
   use score None, level "unknown", and hold for manual review (docs/api.md)
4. Status HELD if score >= case_state.HOLD_THRESHOLD (or unknown), else RELEASED
5. holdEndsAt = 10 business days out when HELD
6. notify.notify_held(case, account) when HELD, store the result in case["notified"]
7. db.put_case(case) and audit.write_audit(caseId, "system", status, detail)
"""

from common.http import ApiError, api_handler, parse_body, require, respond
from common.roles import require_role
from common.samples import sample_case
from common.views import case_for_role


@api_handler
def handler(event, context):
    require_role(event, "client")
    body = parse_body(event)
    require(body, "accountId", "amount", "payee")
    if not isinstance(body["amount"], (int, float)) or body["amount"] <= 0:
        raise ApiError(400, "bad_request", "amount must be a positive number.")

    case = sample_case()  # TODO(Krish): replace with steps 1-7 above
    return respond(case_for_role(case, "client"), 201)
