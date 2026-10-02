"""The case context endpoint and the Ask Claude assistant. Claude is faked; no network."""

import json

import pytest

from common import audit, db
from conftest import body
from fraud_ai import assistant as assistant_ai
from handlers import assistant, case_context

QUESTION = [{"role": "user", "text": "Why was this held?"}]


def ctx(event, role, case_id="case-0001"):
    return case_context.handler(event("case_context", headers={"X-Role": role}, pathParameters={"caseId": case_id}), None)


def ask_event(event, role="fraud", messages=QUESTION, case_id="case-0001"):
    return event("assistant", headers={"X-Role": role}, pathParameters={"caseId": case_id},
                 body=json.dumps({"messages": messages}))


@pytest.fixture
def fake_ask(monkeypatch):
    """Replaces Claude; records what the handler passed in."""
    calls = []

    def fake(role, context, messages):
        calls.append({"role": role, "context": context, "messages": messages})
        return {"reply": "It matches an impostor scam.", "suggestions": ["Who was alerted?"]}

    monkeypatch.setattr(assistant, "ask", fake)
    return calls


# — context —

def test_context_fraud_lists_contacts_by_name(event, seeded):
    data = body(ctx(event, "fraud"))
    assert data["clientName"] == "Margaret Ellis"
    assert data["advisor"]["contactId"]
    kinds = {c["kind"] for c in data["contacts"]}
    assert "advisor" in kinds and "emergency" in kinds
    assert all(c["name"] for c in data["contacts"])


def test_context_advisor_same_shape(event, seeded):
    data = body(ctx(event, "advisor"))
    assert {"accountId", "clientName", "clientAge", "accountOpened", "advisor", "contacts", "contactLog", "advisorNotes"} == data.keys()


def test_context_client_only_gets_advisor(event, seeded):
    data = body(ctx(event, "client"))
    assert list(data) == ["advisor"]


def test_context_unknown_case(event, seeded):
    assert ctx(event, "fraud", "case-nope")["statusCode"] == 404


def test_context_joint_owner_kind(event, seeded):
    case = db.get_case("case-0001")
    db.put_case({**case, "caseId": "case-jo", "accountId": "acc-1005"})
    kinds = {c["contactId"]: c["kind"] for c in body(ctx(event, "fraud", "case-jo"))["contacts"]}
    assert kinds["jo-05"] == "joint_owner"


# — assistant —

def test_assistant_answers_and_audits(event, seeded, fake_ask):
    result = assistant.handler(ask_event(event), None)
    assert result["statusCode"] == 200
    assert body(result) == {"reply": "It matches an impostor scam.", "suggestions": ["Who was alerted?"]}
    rows = audit.list_audit("case-0001")
    assert rows[-1]["action"] == "ASSISTANT_QUESTION" and rows[-1]["detail"] == "Why was this held?"


def test_client_cannot_use_assistant(event, seeded, fake_ask):
    assert assistant.handler(ask_event(event, role="client"), None)["statusCode"] == 403
    assert not fake_ask


@pytest.mark.parametrize("messages", [
    [],
    [{"role": "assistant", "text": "hi"}],
    [{"role": "user", "text": ""}],
    [{"role": "user", "text": "x" * 2001}],
    [{"role": "robot", "text": "hi"}],
    [{"role": "user", "text": "q"}] * 21,
])
def test_assistant_validation(event, seeded, fake_ask, messages):
    result = assistant.handler(ask_event(event, messages=messages), None)
    assert result["statusCode"] == 400
    assert body(result)["error"]["code"] == "bad_request"


def test_assistant_unknown_case(event, seeded, fake_ask):
    assert assistant.handler(ask_event(event, case_id="case-nope"), None)["statusCode"] == 404


def test_advisor_context_hides_suspects_and_audit(event, seeded, fake_ask):
    case = db.get_case("case-0001")
    db.update_case("case-0001", {"risk": {**case["risk"], "doNotNotify": ["ec-01"]}})
    assistant.handler(ask_event(event, role="advisor"), None)
    sent = fake_ask[0]["context"]
    assert "doNotNotify" not in sent["case"]["risk"]
    assert "audit" not in sent["case"]
    assert "ec-01" not in json.dumps(sent)


def test_fraud_context_includes_audit_and_suspects(event, seeded, fake_ask):
    case = db.get_case("case-0001")
    db.update_case("case-0001", {"risk": {**case["risk"], "doNotNotify": ["ec-01"]}})
    assistant.handler(ask_event(event), None)
    sent = fake_ask[0]["context"]
    assert sent["case"]["risk"]["doNotNotify"] == ["ec-01"]
    assert sent["case"]["audit"][-1]["action"] == "ASSISTANT_QUESTION"
    assert sent["history90Days"] is not None
    assert sent["account"]["clientName"] == "Margaret Ellis"


def test_assistant_ai_failure_is_502(event, seeded, monkeypatch):
    def boom(role, context, messages):
        raise RuntimeError("Bedrock down")

    monkeypatch.setattr(assistant, "ask", boom)
    result = assistant.handler(ask_event(event), None)
    assert result["statusCode"] == 502
    assert body(result)["error"]["code"] == "ai_unavailable"


# — fraud_ai.assistant.ask —

def fake_claude(monkeypatch, answer):
    seen = {}

    def converse_json(prompt, system=None, max_tokens=2000):
        seen.update(prompt=prompt, system=system)
        if isinstance(answer, Exception):
            raise answer
        return answer

    monkeypatch.setattr(assistant_ai.bedrock_client, "converse_json", converse_json)
    return seen


def test_ask_trims_suggestions(monkeypatch):
    fake_claude(monkeypatch, {"reply": " Held. ", "suggestions": ["a" * 120, "", "b", "c", "d"]})
    out = assistant_ai.ask("fraud", {"case": {}}, QUESTION)
    assert out["reply"] == "Held."
    assert out["suggestions"] == ["a" * 80, "b", "c"]


def test_ask_bad_suggestions_default_empty(monkeypatch):
    fake_claude(monkeypatch, {"reply": "Held.", "suggestions": "not a list"})
    assert assistant_ai.ask("advisor", {}, QUESTION)["suggestions"] == []


@pytest.mark.parametrize("answer", [{"reply": ""}, {"suggestions": []}, ["not", "a", "dict"]])
def test_ask_raises_on_bad_reply(monkeypatch, answer):
    fake_claude(monkeypatch, answer)
    with pytest.raises(ValueError):
        assistant_ai.ask("fraud", {}, QUESTION)


def test_ask_raises_when_claude_fails(monkeypatch):
    fake_claude(monkeypatch, RuntimeError("Bedrock down"))
    with pytest.raises(RuntimeError):
        assistant_ai.ask("fraud", {}, QUESTION)


def test_ask_prompt_wraps_turns_and_role_rules(monkeypatch):
    seen = fake_claude(monkeypatch, {"reply": "ok", "suggestions": []})
    messages = [{"role": "user", "text": "first"}, {"role": "assistant", "text": "answer"}, {"role": "user", "text": "next"}]
    assistant_ai.ask("advisor", {"case": {"caseId": "case-0001"}}, messages)
    assert "<user_message>first</user_message>" in seen["prompt"]
    assert "<assistant_message>answer</assistant_message>" in seen["prompt"]
    assert "case-0001" in seen["prompt"]
    assert "financial advisors" in seen["system"]
    assert "number on file" in seen["system"]
