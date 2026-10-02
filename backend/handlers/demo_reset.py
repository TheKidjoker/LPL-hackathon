"""POST /demo/reset. Owner: Kaylin.

Deletes every Case and Audit row, then reloads Accounts and Transactions from the seed data,
so the demo can be run again from the start. The seed files come from SEED_DATA_DIR: /opt in
Lambda (the SeedDataLayer, built from data/), the repo's data/ folder locally.
"""

import json
import logging
import os
from pathlib import Path

from common import db
from common.http import api_handler, respond
from common.roles import get_role

logger = logging.getLogger()


def seed_dir():
    return Path(os.environ.get("SEED_DATA_DIR") or Path(__file__).resolve().parents[2] / "data")


@api_handler
def handler(event, context):
    role = get_role(event)
    folder = seed_dir()
    accounts = json.loads((folder / "accounts.json").read_text())
    transactions = json.loads((folder / "transactions.json").read_text())

    cases, audit_rows = db.clear_cases_and_audit()
    loaded = db.load_seed_data(accounts, transactions)
    logger.info("Demo reset by %s: deleted %d cases and %d audit rows, loaded %d accounts", role, cases, audit_rows, loaded)
    return respond({"ok": True, "accountsLoaded": loaded})
