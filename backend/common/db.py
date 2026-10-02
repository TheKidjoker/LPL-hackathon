"""DynamoDB helpers. Owner: Krish. Nobody else calls DynamoDB directly.

Table names come from environment variables set in infra/template.yaml.
Each function below is a stub: replace the body, keep the signature.
"""

import os

ACCOUNTS_TABLE = os.environ.get("ACCOUNTS_TABLE", "")
TRANSACTIONS_TABLE = os.environ.get("TRANSACTIONS_TABLE", "")
CASES_TABLE = os.environ.get("CASES_TABLE", "")
AUDIT_TABLE = os.environ.get("AUDIT_TABLE", "")


def get_account(account_id):
    """Return the Account dict, or None if it does not exist."""
    raise NotImplementedError


def get_history(account_id, days=90):
    """Return the account's Transactions from the last `days` days, newest first."""
    raise NotImplementedError


def put_case(case):
    """Save a new Case."""
    raise NotImplementedError


def get_case(case_id):
    """Return the Case dict, or None if it does not exist."""
    raise NotImplementedError


def update_case(case_id, changes):
    """Apply a dict of top-level field changes to a Case and return the updated Case."""
    raise NotImplementedError


def list_cases_by_status(status=None):
    """Return Cases, filtered by status when given. Uses the StatusIndex."""
    raise NotImplementedError
