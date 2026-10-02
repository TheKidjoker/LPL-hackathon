"""What each role sees in a Case, per the table in docs/api.md. Owner: Krish."""

import copy

CLIENT_FIELDS = ("caseId", "status", "createdAt", "transaction", "holdEndsAt", "decision")
ADVISOR_FIELDS = CLIENT_FIELDS + ("clientName", "accountId", "notified", "risk", "responses")


def case_for_role(case, role):
    if role == "fraud":
        return copy.deepcopy(case)
    if role == "advisor":
        view = {k: copy.deepcopy(case.get(k)) for k in ADVISOR_FIELDS}
        if view.get("risk"):
            view["risk"].pop("doNotNotify", None)
        return view
    view = {k: copy.deepcopy(case.get(k)) for k in CLIENT_FIELDS}
    view["responses"] = [r for r in case.get("responses", []) if r.get("role") == "client"]
    return view


def case_summary(case):
    risk = case.get("risk") or {}
    txn = case.get("transaction") or {}
    return {
        "caseId": case["caseId"],
        "clientName": case.get("clientName"),
        "amount": txn.get("amount"),
        "payeeName": (txn.get("payee") or {}).get("name"),
        "status": case.get("status"),
        "score": risk.get("score"),
        "level": risk.get("level"),
        "createdAt": case.get("createdAt"),
        "holdEndsAt": case.get("holdEndsAt"),
    }
