import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "backend"), str(ROOT / "ai")]


@pytest.fixture
def event():
    """event("get_case") loads events/get_case.json; pass overrides as keyword args."""

    def load(name, **overrides):
        data = json.loads((ROOT / "events" / f"{name}.json").read_text())
        data.update(overrides)
        return data

    return load


def body(result):
    return json.loads(result["body"])
