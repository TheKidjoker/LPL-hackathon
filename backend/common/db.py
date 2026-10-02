"""DynamoDB helpers. Owner: Kaylin. Nobody else calls DynamoDB directly.

Table names come from environment variables set in infra/template.yaml.
DynamoDB returns numbers as Decimal. Every function here takes and returns plain int and float.
"""

import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

ACCOUNTS_TABLE = os.environ.get("ACCOUNTS_TABLE", "")
TRANSACTIONS_TABLE = os.environ.get("TRANSACTIONS_TABLE", "")
CASES_TABLE = os.environ.get("CASES_TABLE", "")
AUDIT_TABLE = os.environ.get("AUDIT_TABLE", "")

_resource = None


def _table(name):
    global _resource
    if not name:
        raise RuntimeError("Table name not set. Set ACCOUNTS_TABLE, TRANSACTIONS_TABLE, CASES_TABLE, AUDIT_TABLE.")
    if _resource is None:
        _resource = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "us-east-1"))
    return _resource.Table(name)


def _from_dynamo(value):
    """Decimal -> int or float, recursively."""
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, dict):
        return {k: _from_dynamo(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_from_dynamo(v) for v in value]
    return value


def _to_dynamo(value):
    """float -> Decimal, recursively. DynamoDB rejects Python floats."""
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {k: _to_dynamo(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_dynamo(v) for v in value]
    return value


def _query_all(table, **kwargs):
    items = []
    while True:
        resp = table.query(**kwargs)
        items += resp["Items"]
        if "LastEvaluatedKey" not in resp:
            return [_from_dynamo(i) for i in items]
        kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]


def _scan_all(table, **kwargs):
    items = []
    while True:
        resp = table.scan(**kwargs)
        items += resp["Items"]
        if "LastEvaluatedKey" not in resp:
            return [_from_dynamo(i) for i in items]
        kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]


def get_account(account_id):
    """Return the Account dict, or None if it does not exist."""
    item = _table(ACCOUNTS_TABLE).get_item(Key={"accountId": account_id}).get("Item")
    return _from_dynamo(item) if item else None


def get_history(account_id, days=90):
    """Return the account's Transactions from the last `days` days, newest first."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return _query_all(
        _table(TRANSACTIONS_TABLE),
        KeyConditionExpression=Key("accountId").eq(account_id) & Key("timestamp").gte(cutoff),
        ScanIndexForward=False,
    )


def put_case(case):
    """Save a new Case."""
    _table(CASES_TABLE).put_item(Item=_to_dynamo(case))


def get_case(case_id):
    """Return the Case dict, or None if it does not exist."""
    item = _table(CASES_TABLE).get_item(Key={"caseId": case_id}).get("Item")
    return _from_dynamo(item) if item else None


def update_case(case_id, changes):
    """Apply a dict of top-level field changes to a Case and return the updated Case.

    Returns None if the Case does not exist. `caseId` cannot be changed.
    """
    changes = {k: v for k, v in changes.items() if k != "caseId"}
    if not changes:
        return get_case(case_id)
    names = {f"#f{i}": field for i, field in enumerate(changes)}
    values = {f":v{i}": _to_dynamo(value) for i, value in enumerate(changes.values())}
    try:
        resp = _table(CASES_TABLE).update_item(
            Key={"caseId": case_id},
            UpdateExpression="SET " + ", ".join(f"#f{i} = :v{i}" for i in range(len(changes))),
            ConditionExpression="attribute_exists(caseId)",
            ExpressionAttributeNames=names,
            ExpressionAttributeValues=values,
            ReturnValues="ALL_NEW",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return None
        raise
    return _from_dynamo(resp["Attributes"])


def append_response(case_id, response, changes=None):
    """Append a Response to a Case's responses in one atomic write, plus any top-level field changes.

    Returns the updated Case, or None if it does not exist.
    """
    changes = {k: v for k, v in (changes or {}).items() if k not in ("caseId", "responses")}
    names = {"#responses": "responses", **{f"#f{i}": field for i, field in enumerate(changes)}}
    values = {":r": [_to_dynamo(response)], ":empty": [],
              **{f":v{i}": _to_dynamo(value) for i, value in enumerate(changes.values())}}
    sets = ["#responses = list_append(if_not_exists(#responses, :empty), :r)"]
    sets += [f"#f{i} = :v{i}" for i in range(len(changes))]
    try:
        resp = _table(CASES_TABLE).update_item(
            Key={"caseId": case_id},
            UpdateExpression="SET " + ", ".join(sets),
            ConditionExpression="attribute_exists(caseId)",
            ExpressionAttributeNames=names,
            ExpressionAttributeValues=values,
            ReturnValues="ALL_NEW",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return None
        raise
    return _from_dynamo(resp["Attributes"])


def list_cases_by_status(status=None):
    """Return Cases, filtered by status when given. Uses the StatusIndex.

    With a status, newest first. Without one, every Case in no set order; the handler sorts.
    """
    table = _table(CASES_TABLE)
    if status is None:
        return _scan_all(table)
    return _query_all(
        table,
        IndexName="StatusIndex",
        KeyConditionExpression=Key("status").eq(status),
        ScanIndexForward=False,
    )


# Audit rows. Called only from common/audit.py.

def put_audit_row(row):
    """Save one audit row. Returns False if a row with the same caseId and timestamp already exists."""
    try:
        _table(AUDIT_TABLE).put_item(
            Item=_to_dynamo(row),
            ConditionExpression="attribute_not_exists(caseId)",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise
    return True


def list_audit_rows(case_id):
    """Return a Case's audit rows, oldest first."""
    return _query_all(_table(AUDIT_TABLE), KeyConditionExpression=Key("caseId").eq(case_id))


# Seed data. Used by scripts/seed_dynamodb.py and handlers/demo_reset.py.

def _clear(name, key_names):
    table = _table(name)
    keys = _scan_all(table, ProjectionExpression=", ".join(f"#k{i}" for i in range(len(key_names))),
                     ExpressionAttributeNames={f"#k{i}": k for i, k in enumerate(key_names)})
    with table.batch_writer() as batch:
        for key in keys:
            batch.delete_item(Key=_to_dynamo(key))
    return len(keys)


def load_seed_data(accounts, transactions):
    """Replace everything in Accounts and Transactions with the given rows. Returns the number of accounts."""
    _clear(ACCOUNTS_TABLE, ["accountId"])
    _clear(TRANSACTIONS_TABLE, ["accountId", "timestamp"])
    with _table(ACCOUNTS_TABLE).batch_writer() as batch:
        for account in accounts:
            batch.put_item(Item=_to_dynamo(account))
    with _table(TRANSACTIONS_TABLE).batch_writer() as batch:
        for txn in transactions:
            batch.put_item(Item=_to_dynamo(txn))
    return len(accounts)


def clear_cases_and_audit():
    """Delete every Case and Audit row. Returns (cases deleted, audit rows deleted)."""
    return _clear(CASES_TABLE, ["caseId"]), _clear(AUDIT_TABLE, ["caseId", "timestamp"])
