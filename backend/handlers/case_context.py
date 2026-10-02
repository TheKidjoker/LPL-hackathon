"""GET /cases/{caseId}/context. Owner: Thomas.

Names and relationships for the people around a case, so views can show names instead of
contact ids. The client only learns who their advisor is.
"""

from common import db
from common.http import ApiError, api_handler, path_param, respond
from common.roles import get_role


def advisor_of(account):
    advisor = (account or {}).get("advisor")
    return {"contactId": advisor["contactId"], "name": advisor.get("name")} if advisor else None


def contacts_of(account):
    account = account or {}
    contacts = []
    advisor = account.get("advisor")
    if advisor:
        contacts.append({"contactId": advisor["contactId"], "name": advisor.get("name"), "relationship": "advisor", "kind": "advisor"})
    emergency = account.get("emergencyContact")
    if emergency:
        contacts.append({**_person(emergency), "kind": "emergency"})
    for owner in account.get("jointOwners") or []:
        contacts.append({**_person(owner), "kind": "joint_owner"})
    return contacts


def _person(p):
    return {"contactId": p["contactId"], "name": p.get("name"), "relationship": p.get("relationship")}


@api_handler
def handler(event, context):
    role = get_role(event)
    case_id = path_param(event, "caseId")

    case = db.get_case(case_id)
    if case is None:
        raise ApiError(404, "not_found", f"No case {case_id}.")
    account = db.get_account(case["accountId"]) or {}

    if role == "client":
        return respond({"advisor": advisor_of(account)})
    return respond({
        "accountId": case["accountId"],
        "clientName": account.get("clientName") or case.get("clientName"),
        "clientAge": account.get("clientAge"),
        "accountOpened": account.get("accountOpened"),
        "advisor": advisor_of(account),
        "contacts": contacts_of(account),
    })
