"""AI lane tests. No network: converse_json is replaced with a fake. Run: python -m pytest"""

import json
from pathlib import Path

import pytest

from fraud_ai import bedrock_client, scam_check_chat, score_withdrawal
from fraud_ai.score import FALLBACK_MEMO, build_prompt, fallback_risk, level_for, validate
from fraud_ai.signals import compute_signals

SCENARIOS = {s["name"]: s for s in json.loads((Path(__file__).parent / "fixtures" / "ai_scenarios.json").read_text())}


def names(signals):
    return {s["name"] for s in signals}


def signals_for(name):
    s = SCENARIOS[name]
    return names(compute_signals(s["account"], s["transaction"], s["history"]))


# --- signals ---------------------------------------------------------------

def test_hero_fires_the_scam_signals():
    assert {"new_payee", "payee_added_recently", "full_liquidation", "senior_client", "first_crypto", "large_vs_history"} <= signals_for("hero_impostor_crypto")


def test_tech_support_late_night_is_unusual_timing():
    assert "unusual_timing" in signals_for("no_advisor_senior_tech_support")


def test_routine_transfer_fires_only_age():
    assert signals_for("normal_monthly_transfer") == {"senior_client"}


def test_small_withdrawal_fires_nothing():
    assert signals_for("normal_small_withdrawal") == set()


def test_known_payee_from_history_is_not_new():
    account = {"knownPayees": []}
    history = [{"type": "withdrawal", "amount": 100, "payee": {"payeeId": "p1", "name": "Bank"}}]
    txn = {"amount": 100, "payee": {"payeeId": "p1", "name": "Bank"}}
    assert "new_payee" not in names(compute_signals(account, txn, history))


def test_signals_survive_missing_fields():
    assert compute_signals({}, {}, []) == []
    assert compute_signals(None, None, None) == []


# --- score validation --------------------------------------------------------

ACCOUNT = {"jointOwners": [{"contactId": "jo-01"}], "emergencyContact": {"contactId": "ec-01"}}


def test_validate_clamps_and_derives_level():
    risk = validate({"score": 140, "level": "low", "memo": "m"}, ACCOUNT, [])
    assert risk["score"] == 100 and risk["level"] == "high"
    assert validate({"score": -5, "memo": "m"}, ACCOUNT, [])["score"] == 0


@pytest.mark.parametrize("score,level", [(0, "low"), (39, "low"), (40, "medium"), (69, "medium"), (70, "high"), (None, "unknown")])
def test_level_thresholds(score, level):
    assert level_for(score) == level


def test_validate_merges_signals_and_caps_claude_extras():
    rule = [{"name": "new_payee", "detail": "rule"}]
    extra = [{"name": "new_payee", "detail": "dup"}] + [{"name": f"x{i}", "detail": "d"} for i in range(6)]
    risk = validate({"score": 80, "memo": "m", "signals": extra}, ACCOUNT, rule)
    assert risk["signals"][0] == {"name": "new_payee", "detail": "rule"}
    assert len(risk["signals"]) == 4  # rule signal + 3 new extras from Claude's first 4


def test_validate_drops_unknown_do_not_notify_ids():
    risk = validate({"score": 90, "memo": "m", "doNotNotify": ["jo-01", "adv-01", "made-up"]}, ACCOUNT, [])
    assert risk["doNotNotify"] == ["jo-01"]


@pytest.mark.parametrize("raw", [{"score": "high", "memo": "m"}, {"score": 50, "memo": ""}, {"score": 50}, ["not", "a", "dict"]])
def test_validate_rejects_bad_answers(raw):
    with pytest.raises(ValueError):
        validate(raw, ACCOUNT, [])


def test_score_withdrawal_returns_exact_keys(monkeypatch):
    monkeypatch.setattr(bedrock_client, "converse_json", lambda *a, **k: {"score": 92, "memo": "memo", "signals": [], "doNotNotify": []})
    s = SCENARIOS["hero_impostor_crypto"]
    risk = score_withdrawal(s["account"], s["transaction"], s["history"])
    assert set(risk) == {"score", "level", "signals", "memo", "doNotNotify"}
    assert risk["level"] == "high" and "first_crypto" in names(risk["signals"])


def test_score_withdrawal_raises_when_claude_fails(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("throttled")

    monkeypatch.setattr(bedrock_client, "converse_json", boom)
    with pytest.raises(RuntimeError):
        score_withdrawal({}, {}, [])


def test_fallback_risk_matches_api_md():
    risk = fallback_risk([{"name": "new_payee", "detail": "d"}])
    assert risk == {"score": None, "level": "unknown", "signals": [{"name": "new_payee", "detail": "d"}], "memo": FALLBACK_MEMO, "doNotNotify": []}


def test_prompt_fences_client_note_as_data():
    s = SCENARIOS["hero_impostor_crypto"]
    prompt = build_prompt(s["account"], s["transaction"], s["history"], [])
    note = s["transaction"]["clientNote"]
    assert f"<client_note>\n{note}\n</client_note>" in prompt
    for placeholder in ("$account", "$transaction", "$history", "$signals", "$client_note", "$advisor_note", "$contacts"):
        assert placeholder not in prompt


# --- scam-check chat -------------------------------------------------------

def test_chat_passes_through_a_good_reply(monkeypatch):
    monkeypatch.setattr(bedrock_client, "converse_json", lambda *a, **k: {"reply": "Did someone call you?", "riskUpdate": None, "done": False})
    assert scam_check_chat({}, []) == {"reply": "Did someone call you?", "riskUpdate": None, "done": False}


def test_chat_falls_back_to_fixed_question_on_failure(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("down")

    monkeypatch.setattr(bedrock_client, "converse_json", boom)
    out = scam_check_chat({}, [{"role": "assistant", "text": "q1"}, {"role": "client", "text": "yes"}])
    assert out["done"] is False and out["riskUpdate"] is None and "secret" in out["reply"]


def test_chat_forces_finish_after_max_turns(monkeypatch):
    monkeypatch.setattr(bedrock_client, "converse_json", lambda *a, **k: {"reply": "Thanks, the fraud team will follow up.", "riskUpdate": 140, "done": False})
    messages = [{"role": "client", "text": "a"}] * 4
    out = scam_check_chat({}, messages)
    assert out["done"] is True and out["riskUpdate"] == 100
