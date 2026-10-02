"""Kaylin's handlers against in-memory tables loaded with data/. Claude is faked."""

import json
from datetime import date

import pytest

from common import db
from conftest import ROOT, body
from handlers import get_case, list_cases, post_response, submit_withdrawal

SCENARIOS = {s["accountId"]: s["request"] for s in json.loads((ROOT / "data" / "scenarios.json").read_text())}


def risk(score, level, do_not_notify=()):
    return {"score": score, "level": level, "signals": [], "memo": "memo", "doNotNotify": list(do_not_notify)}


def submit(event, account_id, **changes):
    request = {**SCENARIOS[account_id], **changes}
    return submit_withdrawal.handler(event("submit_withdrawal", body=json.dumps(request)), None)


def fraud_view(event, case_id):
    return body(get_case.handler(event("get_case", pathParameters={"caseId": case_id}), None))


@pytest.fixture
def scored(monkeypatch):
    """scored(risk) makes score_withdrawal return it; scored(Exception) makes it raise."""

    def use(result):
        def fake(account, transaction, history):
            if isinstance(result, type) and issubclass(result, Exception):
                raise result("Bedrock down")
            return result

        monkeypatch.setattr(submit_withdrawal, "score_withdrawal", fake)

    return use


def test_high_score_holds_and_alerts(event, seeded, scored):
    scored(risk(92, "high"))
    result = submit(event, "acc-1001")
    assert result["statusCode"] == 201
    client = body(result)
    assert client["status"] == "HELD" and client["holdEndsAt"]

    case = fraud_view(event, client["caseId"])
    assert case["clientName"] == "Margaret Ellis"
    assert case["transaction"]["payee"]["name"] == "CoinVault Exchange"
    assert case["transaction"]["amount"] == 180000
    assert sorted(case["notified"]) == sorted(["client", "fraud-team", "adv-01", "ec-01"])
    assert [a["action"] for a in case["audit"]] == ["RECEIVED", "HELD"]
    assert case["audit"][-1]["detail"] == "Risk score 92"


def test_low_score_releases_without_alerts(event, seeded, scored):
    scored(risk(12, "low"))
    case = fraud_view(event, body(submit(event, "acc-1004"))["caseId"])
    assert case["status"] == "RELEASED"
    assert case["holdEndsAt"] is None and case["notified"] == []
    assert [a["action"] for a in case["audit"]] == ["RECEIVED", "RELEASED"]


def test_claude_failure_holds_for_manual_review(event, seeded, scored):
    scored(RuntimeError)
    case = fraud_view(event, body(submit(event, "acc-1003"))["caseId"])
    assert case["status"] == "HELD"
    assert case["risk"]["score"] is None and case["risk"]["level"] == "unknown"
    assert case["risk"]["memo"] == "Automated review unavailable. Held for manual review."
    assert case["audit"][-1]["detail"] == "Risk score unavailable"


def test_do_not_notify_skips_the_scammer(event, seeded, scored):
    scored(risk(95, "high", do_not_notify=["jo-05", "adv-03"]))
    case = fraud_view(event, body(submit(event, "acc-1005"))["caseId"])
    assert "adv-03" not in case["notified"] and "jo-05" not in case["notified"]
    assert "ec-05" in case["notified"]


def test_known_payee_keeps_its_id(event, seeded, scored):
    scored(risk(10, "low"))
    case = fraud_view(event, body(submit(event, "acc-1002"))["caseId"])
    assert case["transaction"]["payee"]["payeeId"] == "pay-202"


def test_submit_validation(event, seeded, scored):
    scored(risk(10, "low"))
    assert submit(event, "acc-1001", accountId="acc-9999")["statusCode"] == 404
    assert submit(event, "acc-1001", amount=True)["statusCode"] == 400
    assert submit(event, "acc-1001", payee={"name": "X", "type": "cash"})["statusCode"] == 400
    assert submit(event, "acc-1001", channel="fax")["statusCode"] == 400


def test_hold_end_date_counts_business_days():
    assert submit_withdrawal.hold_end_date(date(2026, 10, 2)) == "2026-10-16"  # Friday
    assert submit_withdrawal.hold_end_date(date(2026, 10, 3)) == "2026-10-16"  # Saturday


def test_list_cases_puts_holds_first_newest_first(event, tables):
    for case_id, status, created in [
        ("c1", "RELEASED", "2026-10-02T15:00:00Z"),
        ("c2", "HELD", "2026-10-02T10:00:00Z"),
        ("c3", "HELD", "2026-10-02T12:00:00Z"),
        ("c4", "ESCALATED", "2026-10-02T11:00:00Z"),
    ]:
        db.put_case({"caseId": case_id, "status": status, "createdAt": created})

    everything = body(list_cases.handler(event("list_cases", queryStringParameters=None), None))["cases"]
    assert [c["caseId"] for c in everything] == ["c3", "c2", "c4", "c1"]
    held = body(list_cases.handler(event("list_cases"), None))["cases"]
    assert [c["caseId"] for c in held] == ["c3", "c2"]


def test_get_case_404_and_client_cannot_see_list(event, seeded):
    missing = get_case.handler(event("get_case", pathParameters={"caseId": "case-nope"}), None)
    assert missing["statusCode"] == 404 and body(missing)["error"]["code"] == "not_found"
    assert list_cases.handler(event("list_cases", headers={"X-Role": "client"}), None)["statusCode"] == 403


def respond_as(event, role, kind, text, case_id="case-0001"):
    request = event("post_response", headers={"X-Role": role}, pathParameters={"caseId": case_id},
                    body=json.dumps({"kind": kind, "text": text}))
    return post_response.handler(request, None)


def test_responses_are_saved_and_audited(event, seeded):
    client = body(respond_as(event, "client", "deny", "I did not request this. Someone called me."))
    assert [r["kind"] for r in client["responses"]] == ["deny"]

    advisor = body(respond_as(event, "advisor", "note", "This isn't like her. Calling her now."))
    assert [r["kind"] for r in advisor["responses"]] == ["deny", "note"]
    assert advisor["status"] == "HELD"  # responses never change the status

    case = fraud_view(event, "case-0001")
    assert [r["role"] for r in case["responses"]] == ["client", "advisor"]
    assert [(a["actor"], a["action"]) for a in case["audit"]] == [("client", "DENY"), ("advisor", "NOTE")]

    # The client only ever sees their own responses
    again = body(respond_as(event, "client", "emergency_contact", "Susan Ellis · 555-0142"))
    assert [r["kind"] for r in again["responses"]] == ["deny", "emergency_contact"]


def test_response_validation(event, seeded):
    assert respond_as(event, "advisor", "deny", "no")["statusCode"] == 400
    assert respond_as(event, "client", "note", "hi")["statusCode"] == 400
    assert respond_as(event, "client", "deny", "x" * 2001)["statusCode"] == 400
    assert respond_as(event, "fraud", "note", "hi")["statusCode"] == 403
    missing = respond_as(event, "client", "deny", "no", case_id="case-nope")
    assert missing["statusCode"] == 404


def test_scam_check_chat(event, seeded, monkeypatch):
    seen = []

    def fake_chat(case, messages):
        seen.append(messages)
        turn = sum(1 for m in messages if m["role"] == "client")
        if turn < 2:
            return {"reply": f"Question {turn + 1}?", "riskUpdate": None, "done": False}
        return {"reply": "This matches a common scam. The fraud team will contact you in the app.", "riskUpdate": 88, "done": True}

    monkeypatch.setattr(post_response, "scam_check_chat", fake_chat)

    first = body(respond_as(event, "client", "chat", "Yes, someone called me"))
    assert first["responses"][-1]["chatReply"] == "Question 2?" and first["responses"][-1]["done"] is False
    assert seen[0] == [{"role": "assistant", "text": "Did someone contact you first?"},
                       {"role": "client", "text": "Yes, someone called me"}]

    last = body(respond_as(event, "client", "chat", "Yes, they said keep it secret"))
    assert last["responses"][-1]["done"] is True
    assert seen[1][2:] == [{"role": "assistant", "text": "Question 2?"},
                           {"role": "client", "text": "Yes, they said keep it secret"}]
    assert "risk" not in last  # the client never sees the score

    case = fraud_view(event, "case-0001")
    assert case["risk"]["signals"][-1]["name"] == "scam_check_chat"
    assert "88/100" in case["risk"]["signals"][-1]["detail"]
    assert case["status"] == "HELD"
    assert case["audit"][-1]["action"] == "SCAM_CHECK_DONE"

    assert respond_as(event, "client", "chat", "one more")["statusCode"] == 409
