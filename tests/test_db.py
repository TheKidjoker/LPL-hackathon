"""db.py and audit.py against in-memory DynamoDB (moto). Tables match infra/template.yaml."""

import json
from datetime import datetime, timedelta, timezone

from common import audit, db
from conftest import ROOT

def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def make_case(case_id, status, created_at, score=92.5):
    return {"caseId": case_id, "status": status, "createdAt": created_at, "risk": {"score": score, "signals": []},
            "transaction": {"amount": 180000}, "decision": None}


def test_account_roundtrip_returns_plain_numbers(tables):
    accounts = json.loads((ROOT / "data" / "accounts.json").read_text())
    transactions = json.loads((ROOT / "data" / "transactions.json").read_text())
    assert db.load_seed_data(accounts, transactions) == len(accounts) == 10

    account = db.get_account("acc-1001")
    assert account == accounts[0]
    assert type(account["balance"]) is int and type(account["clientAge"]) is int
    assert db.get_account("acc-9999") is None


def test_get_history_filters_by_days_newest_first(tables):
    now = datetime.now(timezone.utc)
    rows = [{"accountId": "acc-1", "timestamp": iso(now - timedelta(days=d)), "amount": d} for d in (1, 30, 89, 120)]
    db.load_seed_data([], rows)

    history = db.get_history("acc-1")
    assert [h["amount"] for h in history] == [1, 30, 89]
    assert [h["amount"] for h in db.get_history("acc-1", days=10)] == [1]
    assert db.get_history("acc-2") == []


def test_case_put_get_update(tables):
    db.put_case(make_case("case-1", "HELD", "2026-10-02T14:05:00Z"))
    case = db.get_case("case-1")
    assert case["risk"]["score"] == 92.5 and type(case["risk"]["score"]) is float
    assert case["decision"] is None

    decision = {"action": "release", "by": "fraud", "at": "2026-10-03T10:00:00Z", "note": "ok"}
    updated = db.update_case("case-1", {"status": "RELEASED", "decision": decision, "holdEndsAt": None})
    assert updated["status"] == "RELEASED" and updated["decision"] == decision and updated["holdEndsAt"] is None
    assert db.get_case("case-1") == updated

    assert db.get_case("case-404") is None
    assert db.update_case("case-404", {"status": "RELEASED"}) is None


def test_list_cases_by_status(tables):
    db.put_case(make_case("case-1", "HELD", "2026-10-02T10:00:00Z"))
    db.put_case(make_case("case-2", "HELD", "2026-10-02T12:00:00Z"))
    db.put_case(make_case("case-3", "RELEASED", "2026-10-02T11:00:00Z"))

    assert [c["caseId"] for c in db.list_cases_by_status("HELD")] == ["case-2", "case-1"]
    assert {c["caseId"] for c in db.list_cases_by_status()} == {"case-1", "case-2", "case-3"}
    assert db.list_cases_by_status("ESCALATED") == []


def test_audit_rows_in_order_and_never_overwritten(tables, monkeypatch):
    frozen = datetime(2026, 10, 2, 14, 5, 7, 123000, tzinfo=timezone.utc)

    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return frozen

    monkeypatch.setattr(audit, "datetime", FrozenDatetime)
    first = audit.write_audit("case-1", "system", "HELD", "Risk score 92")
    second = audit.write_audit("case-1", "fraud", "RELEASED")

    assert first["timestamp"] == "2026-10-02T14:05:07.123Z"
    assert second["timestamp"] == "2026-10-02T14:05:07.124Z"
    assert audit.list_audit("case-1") == [first, second]
    assert audit.list_audit("case-2") == []


def test_clear_cases_and_audit_leaves_accounts(tables):
    db.load_seed_data([{"accountId": "acc-1"}], [])
    db.put_case(make_case("case-1", "HELD", "2026-10-02T10:00:00Z"))
    audit.write_audit("case-1", "system", "HELD")

    assert db.clear_cases_and_audit() == (1, 1)
    assert db.get_case("case-1") is None and audit.list_audit("case-1") == []
    assert db.get_account("acc-1") is not None
