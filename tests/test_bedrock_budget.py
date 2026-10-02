"""The Bedrock client's time budget: hedge to the fallback model, never exceed the cap."""

import time

import pytest

from fraud_ai import bedrock_client


class TimedBedrock:
    """Fake client where each model answers after a set delay, or raises."""

    def __init__(self, delays):
        self.delays, self.calls = delays, []

    def converse(self, modelId, **kwargs):
        self.calls.append(modelId)
        delay = self.delays[modelId]
        if isinstance(delay, Exception):
            raise delay
        time.sleep(delay)
        return {"output": {"message": {"content": [{"text": f"from {modelId}"}]}}}


@pytest.fixture
def fast_budget(monkeypatch):
    monkeypatch.setattr(bedrock_client, "HEDGE_AFTER", 0.2)
    monkeypatch.setattr(bedrock_client, "TOTAL_BUDGET", 0.6)


def use(monkeypatch, fake):
    monkeypatch.setattr(bedrock_client, "_bedrock", lambda: fake)


def test_main_model_answers_without_hedging(monkeypatch, fast_budget):
    fake = TimedBedrock({bedrock_client.MODEL_ID: 0.05, bedrock_client.FALLBACK_MODEL_ID: 0.05})
    use(monkeypatch, fake)
    assert bedrock_client.converse("hi") == f"from {bedrock_client.MODEL_ID}"
    assert fake.calls == [bedrock_client.MODEL_ID]


def test_slow_main_model_is_hedged_and_fallback_wins(monkeypatch, fast_budget):
    fake = TimedBedrock({bedrock_client.MODEL_ID: 1.0, bedrock_client.FALLBACK_MODEL_ID: 0.05})
    use(monkeypatch, fake)
    start = time.monotonic()
    assert bedrock_client.converse("hi") == f"from {bedrock_client.FALLBACK_MODEL_ID}"
    assert time.monotonic() - start < 0.5


def test_failed_main_model_falls_back_at_once(monkeypatch, fast_budget):
    fake = TimedBedrock({bedrock_client.MODEL_ID: RuntimeError("throttled"), bedrock_client.FALLBACK_MODEL_ID: 0.05})
    use(monkeypatch, fake)
    start = time.monotonic()
    assert bedrock_client.converse("hi") == f"from {bedrock_client.FALLBACK_MODEL_ID}"
    assert time.monotonic() - start < 0.2


def test_gives_up_within_the_budget(monkeypatch, fast_budget):
    fake = TimedBedrock({bedrock_client.MODEL_ID: 2.0, bedrock_client.FALLBACK_MODEL_ID: 2.0})
    use(monkeypatch, fake)
    start = time.monotonic()
    with pytest.raises(TimeoutError):
        bedrock_client.converse("hi")
    assert time.monotonic() - start < 0.9


def test_both_models_failing_raises_the_last_error(monkeypatch, fast_budget):
    fake = TimedBedrock({bedrock_client.MODEL_ID: RuntimeError("a"), bedrock_client.FALLBACK_MODEL_ID: RuntimeError("b")})
    use(monkeypatch, fake)
    with pytest.raises(RuntimeError, match="b"):
        bedrock_client.converse("hi")
