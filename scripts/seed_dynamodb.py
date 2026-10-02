"""Load /data into the deployed tables. Owner: Kaylin.

    python scripts/seed_dynamodb.py

Expected files (shapes in docs/api.md):
    data/accounts.json       list of Account
    data/transactions.json   list of Transaction (history for every account)

Table names: set ACCOUNTS_TABLE and TRANSACTIONS_TABLE to the sam deploy outputs.
Share the loading code with backend/handlers/demo_reset.py.
"""

import os

os.environ.setdefault("AWS_PROFILE", "lpl-hackathon")


def main():
    # TODO(Kaylin): read data/*.json, batch-write to the tables (floats -> Decimal)
    raise NotImplementedError


if __name__ == "__main__":
    main()
