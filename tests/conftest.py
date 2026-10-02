import json
import os
import sys
from pathlib import Path

import boto3
import pytest
from moto import mock_aws

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "backend"), str(ROOT / "ai")]
os.environ.setdefault("SEED_DATA_DIR", str(ROOT / "data"))  # /opt in Lambda
os.environ.setdefault("ALLOW_ROLE_HEADER", "true")  # tests send X-Role; the deployed stack uses Cognito

from common import db  # noqa: E402


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


TABLES = {
    "ACCOUNTS_TABLE": ("Accounts", [("accountId", "HASH")]),
    "TRANSACTIONS_TABLE": ("Transactions", [("accountId", "HASH"), ("timestamp", "RANGE")]),
    "CASES_TABLE": ("Cases", [("caseId", "HASH")]),
    "AUDIT_TABLE": ("Audit", [("caseId", "HASH"), ("timestamp", "RANGE")]),
}


@pytest.fixture
def tables(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    with mock_aws():
        client = boto3.client("dynamodb", region_name="us-east-1")
        for var, (name, keys) in TABLES.items():
            attrs = {k for k, _ in keys}
            extra = {}
            if name == "Cases":
                attrs |= {"status", "createdAt"}
                extra["GlobalSecondaryIndexes"] = [{
                    "IndexName": "StatusIndex",
                    "KeySchema": [{"AttributeName": "status", "KeyType": "HASH"},
                                  {"AttributeName": "createdAt", "KeyType": "RANGE"}],
                    "Projection": {"ProjectionType": "ALL"},
                }]
            client.create_table(
                TableName=name,
                KeySchema=[{"AttributeName": k, "KeyType": t} for k, t in keys],
                AttributeDefinitions=[{"AttributeName": a, "AttributeType": "S"} for a in sorted(attrs)],
                BillingMode="PAY_PER_REQUEST",
                **extra,
            )
            monkeypatch.setattr(db, var, name)
        monkeypatch.setattr(db, "_resource", None)
        yield


@pytest.fixture
def seeded(tables):
    """In-memory tables loaded with data/ and the sample hero Case (case-0001)."""
    from common.samples import sample_case

    accounts = json.loads((ROOT / "data" / "accounts.json").read_text())
    transactions = json.loads((ROOT / "data" / "transactions.json").read_text())
    db.load_seed_data(accounts, transactions)
    case = sample_case()
    case.pop("audit")
    db.put_case(case)
