"""POST /scam-check: a client asks Juno whether a contact is a scam. Claude is faked; no network."""

import json

import pytest

from common import db
from conftest import body
from fraud_ai import bedrock_client, contact_check
from handlers import scam_check

SCAM = ("A man from the bank security department called. He says my account was hacked "
        "and I need to move my money to a safe account today.")
ANSWER = {"verdict": "likely_scam", "scamType": "Bank impersonation", "reply": "This is a scam. It is safe to hang up.",
          "nextSteps": ["Hang up", "Call the number on your statement"], "suggestions": ["What if they call back?"]}


def check_event(event, role="client", **fields):
    payload = {"accountId": "acc-1001", "checkId": "chk-1", "channel": "phone",
               "messages": [{"role": "user", "text": SCAM}], **fields}
    return event("scam_check", headers={"X-Role": role}, body=json.dumps(payload))


@pytest.fixture
def fake_claude(monkeypatch):
    calls = []

    def fake(prompt, system=None, max_tokens=0):
        calls.append(prompt)
        return dict(ANSWER)

    monkeypatch.setattr(bedrock_client, "converse_json", fake)
    return calls


def juno_entries(account_id="acc-1001"):
    return [e for e in db.get_account(account_id)["contactLog"] if e.get("channel") == "juno"]


def test_returns_verdict_and_logs_it(event, seeded, fake_claude):
    result = scam_check.handler(check_event(event), None)
    assert result["statusCode"] == 200
    data = body(result)
    assert data["verdict"] == "likely_scam" and data["fallback"] is False
    assert data["nextSteps"] == ANSWER["nextSteps"]
    [entry] = juno_entries()
    assert entry["id"] == "chk-1" and entry["party"] == "client" and entry["verdict"] == "likely_scam"
    assert "likely a scam (Bank impersonation)" in entry["summary"]


def test_same_check_updates_one_entry(event, seeded, fake_claude):
    before = len(db.get_account("acc-1001")["contactLog"])
    messages = [{"role": "user", "text": SCAM}, {"role": "assistant", "text": "Is he still on the phone?"},
                {"role": "user", "text": "Yes"}]
    scam_check.handler(check_event(event), None)
    scam_check.handler(check_event(event, messages=messages), None)
    assert len(db.get_account("acc-1001")["contactLog"]) == before + 1
    assert "after 2 messages" in juno_entries()[0]["summary"]


def test_prompt_has_advisor_name_but_no_account_details(event, seeded, fake_claude):
    scam_check.handler(check_event(event), None)
    prompt = fake_claude[0]
    assert "Daniel Reyes" in prompt and "Margaret" in prompt
    assert "acc-1001" not in prompt and "balance" not in prompt
    assert f"<client_message>{SCAM}</client_message>" in prompt


def test_staff_cannot_call_it(event, seeded, fake_claude):
    assert scam_check.handler(check_event(event, role="advisor"), None)["statusCode"] == 403


def test_unknown_account_and_bad_channel(event, seeded, fake_claude):
    assert scam_check.handler(check_event(event, accountId="acc-nope"), None)["statusCode"] == 404
    assert scam_check.handler(check_event(event, channel="fax"), None)["statusCode"] == 400


def test_claude_failure_gives_safe_advice_not_an_error(event, seeded, monkeypatch):
    def boom(*a, **k):
        raise TimeoutError("slow")

    monkeypatch.setattr(bedrock_client, "converse_json", boom)
    result = scam_check.handler(check_event(event), None)
    assert result["statusCode"] == 200
    data = body(result)
    assert data["fallback"] is True and data["verdict"] == "suspicious"
    assert any("statement" in s for s in data["nextSteps"])


def test_bad_verdict_falls_back(monkeypatch):
    monkeypatch.setattr(bedrock_client, "converse_json", lambda *a, **k: {"verdict": "maybe", "reply": "hm"})
    assert contact_check.check_contact({}, "phone", [{"role": "user", "text": "hi"}])["fallback"] is True


def test_need_more_has_no_steps(monkeypatch):
    monkeypatch.setattr(bedrock_client, "converse_json",
                        lambda *a, **k: {**ANSWER, "verdict": "need_more", "scamType": None})
    result = contact_check.check_contact({}, "text", [{"role": "user", "text": "I got a text"}])
    assert result["verdict"] == "need_more" and result["nextSteps"] == [] and result["scamType"] is None
