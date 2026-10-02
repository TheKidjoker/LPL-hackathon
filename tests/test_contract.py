"""Checks every handler against the shapes in docs/api.md. Run: python -m pytest"""

from conftest import body
from handlers import demo_reset, get_case, list_cases, post_decision, post_response, submit_withdrawal

CASE_KEYS = {"caseId", "status", "createdAt", "transaction", "holdEndsAt", "decision"}


def test_submit_returns_client_view(event, seeded, monkeypatch):
    from common.samples import SAMPLE_CASE

    monkeypatch.setattr(submit_withdrawal, "score_withdrawal", lambda *a: dict(SAMPLE_CASE["risk"]))
    result = submit_withdrawal.handler(event("submit_withdrawal"), None)
    assert result["statusCode"] == 201
    case = body(result)
    assert CASE_KEYS <= case.keys()
    assert "risk" not in case and "audit" not in case


def test_submit_rejects_wrong_role(event):
    result = submit_withdrawal.handler(event("submit_withdrawal", headers={"X-Role": "advisor"}), None)
    assert result["statusCode"] == 403
    assert body(result)["error"]["code"] == "forbidden"


def test_submit_rejects_bad_body(event):
    result = submit_withdrawal.handler(event("submit_withdrawal", body='{"accountId": "acc-1001"}'), None)
    assert result["statusCode"] == 400


def test_list_cases_returns_summaries(event, seeded):
    result = list_cases.handler(event("list_cases"), None)
    assert result["statusCode"] == 200
    summary = body(result)["cases"][0]
    assert {"caseId", "clientName", "amount", "payeeName", "status", "score", "level"} <= summary.keys()


def test_get_case_filters_by_role(event, seeded):
    fraud = body(get_case.handler(event("get_case"), None))
    advisor = body(get_case.handler(event("get_case", headers={"X-Role": "advisor"}), None))
    client = body(get_case.handler(event("get_case", headers={"X-Role": "client"}), None))
    assert "audit" in fraud and "doNotNotify" in fraud["risk"]
    assert "audit" not in advisor and "doNotNotify" not in advisor["risk"]
    assert "risk" not in client and "clientName" not in client


def test_client_response_is_added(event):
    case = body(post_response.handler(event("post_response"), None))
    assert case["responses"][-1]["kind"] == "deny"


def test_advisor_cannot_deny(event):
    result = post_response.handler(event("post_response", headers={"X-Role": "advisor"}), None)
    assert result["statusCode"] == 400


def test_only_fraud_can_decide(event):
    result = post_decision.handler(event("post_decision", headers={"X-Role": "advisor"}), None)
    assert result["statusCode"] == 403


def test_decision_moves_status(event):
    case = body(post_decision.handler(event("post_decision"), None))
    assert case["status"] == "ESCALATED"
    assert case["decision"]["action"] == "escalate"


def test_demo_reset(event):
    assert body(demo_reset.handler(event("demo_reset"), None))["ok"] is True


def test_ai_stub_shapes():
    from fraud_ai import scam_check_chat, score_withdrawal

    risk = score_withdrawal({}, {}, [])
    assert {"score", "level", "signals", "memo", "doNotNotify"} == risk.keys()
    chat = scam_check_chat({}, [])
    assert {"reply", "riskUpdate", "done"} == chat.keys()
