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
    seeded = db.load_seed_cases(*seed_cases(folder))
    logger.info("Demo reset by %s: deleted %d cases and %d audit rows, loaded %d accounts and %d pre-seeded cases",
                role, cases, audit_rows, loaded, seeded)
    return respond({"ok": True, "accountsLoaded": loaded, "casesLoaded": seeded})


def seed_cases(folder):
    """Pre-seeded Cases and audit rows, so the queue isn't empty when the demo starts. Optional files."""
    read = lambda name: json.loads((folder / name).read_text()) if (folder / name).exists() else []
    return read("cases.json"), read("audit.json")
