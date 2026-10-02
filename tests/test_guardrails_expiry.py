"""Bedrock Guardrail on AI output, and the scheduled hold-expiry check."""

from common import audit, db
from fraud_ai import bedrock_client
from handlers import hold_expiry


class FakeBedrock:
    def __init__(self, response=None, error=None):
        self.response, self.error, self.calls = response, error, []

    def apply_guardrail(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.response


def use_guardrail(monkeypatch, fake):
    monkeypatch.setattr(bedrock_client, "GUARDRAIL_ID", "gr-123")
    monkeypatch.setattr(bedrock_client, "_bedrock", lambda: fake)


def test_guard_output_is_a_no_op_without_a_guardrail(monkeypatch):
    monkeypatch.setattr(bedrock_client, "GUARDRAIL_ID", "")
    assert bedrock_client.guard_output("hello") == "hello"


def test_guard_output_passes_clean_text(monkeypatch):
    fake = FakeBedrock({"action": "NONE", "outputs": []})
    use_guardrail(monkeypatch, fake)
    assert bedrock_client.guard_output("The payee was added two hours earlier.") == "The payee was added two hours earlier."
    assert fake.calls[0]["source"] == "OUTPUT"


def test_guard_output_replaces_blocked_text(monkeypatch):
    fake = FakeBedrock({"action": "GUARDRAIL_INTERVENED", "outputs": [{"text": "Juno can't give investment advice."}]})
    use_guardrail(monkeypatch, fake)
    assert bedrock_client.guard_output("Buy Bitcoin now.") == "Juno can't give investment advice."


def test_guard_output_fails_open_when_the_guardrail_is_down(monkeypatch):
    use_guardrail(monkeypatch, FakeBedrock(error=RuntimeError("throttled")))
    assert bedrock_client.guard_output("memo text") == "memo text"


def test_hold_expiry_escalates_only_ended_holds(seeded):
    # case-0001 is HELD until 2026-10-16 (5:00 PM ET = 21:00 UTC).
    assert hold_expiry.handler({"asOf": "2026-10-16T20:59:00Z"}, None)["escalated"] == []
    assert db.get_case("case-0001")["status"] == "HELD"

    result = hold_expiry.handler({"asOf": "2026-10-16T21:00:00Z"}, None)
    assert result["escalated"] == ["case-0001"]
    assert db.get_case("case-0001")["status"] == "ESCALATED"
    assert audit.list_audit("case-0001")[-1]["action"] == "ESCALATED"


def test_hold_expiry_leaves_decided_cases_alone(seeded):
    db.update_case("case-0001", {"status": "RELEASED", "holdEndsAt": None})
    assert hold_expiry.handler({"asOf": "2026-12-01T00:00:00Z"}, None)["escalated"] == []
    assert db.get_case("case-0001")["status"] == "RELEASED"


def test_blocked_question_refuses_advice_without_calling_claude(monkeypatch):
    from fraud_ai import assistant

    monkeypatch.setattr(bedrock_client, "QUESTION_GUARDRAIL_ID", "gq-1")
    fake = FakeBedrock({"action": "GUARDRAIL_INTERVENED", "outputs": [{"text": "Juno can't give investment advice."}]})
    monkeypatch.setattr(bedrock_client, "_bedrock", lambda: fake)
    monkeypatch.setattr(bedrock_client, "converse_json", lambda *a, **k: (_ for _ in ()).throw(AssertionError("Claude was called")))
    result = assistant.ask("fraud", {}, [{"role": "user", "text": "Should she buy an index fund instead?"}])
    assert result["reply"] == "Juno can't give investment advice."
    assert fake.calls[0]["source"] == "INPUT"


def test_blocked_question_allows_case_questions(monkeypatch):
    monkeypatch.setattr(bedrock_client, "QUESTION_GUARDRAIL_ID", "gq-1")
    monkeypatch.setattr(bedrock_client, "_bedrock", lambda: FakeBedrock({"action": "NONE"}))
    assert bedrock_client.blocked_question("Why was this held?") is None
