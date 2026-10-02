"""Generate data/accounts.json, data/transactions.json, and data/scenarios.json. Owner: Kaylin.

    python scripts/make_seed_data.py

Edit the accounts and history rules here, then re-run. Output is the same every run (fixed random seed).
Shapes are in docs/api.md. All names and numbers are fake.

- accounts.json      six Accounts: the hero, three normal, a scammer joint owner, and one with no advisor
- transactions.json  90 days of normal history for every account, ending the day before the demo
- scenarios.json     the POST /withdrawals request for each account's demo withdrawal, with the expected level
"""

import json
import random
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
HISTORY_END = date(2026, 10, 1)  # day before the demo withdrawals
HISTORY_DAYS = 90

rng = random.Random(2166)


def payee(payee_id, name, type_, added_at):
    return {"payeeId": payee_id, "name": name, "type": type_, "addedAt": added_at}


# Payees reused across accounts and history.
SSA = payee("pay-001", "U.S. Treasury SSA benefit", "bank", "2010-01-01T00:00:00Z")

ACCOUNTS = [
    {
        # Hero: 22-year client, full balance to a crypto payee added two hours before the request.
        "accountId": "acc-1001",
        "clientName": "Margaret Ellis",
        "clientAge": 78,
        "accountOpened": "2004-03-15",
        "balance": 180000,
        "advisor": {"contactId": "adv-01", "name": "Daniel Reyes"},
        "emergencyContact": {"contactId": "ec-01", "name": "Susan Ellis", "relationship": "daughter"},
        "jointOwners": [],
        "knownPayees": [
            payee("pay-100", "First Harbor Bank checking", "bank", "2011-06-01T00:00:00Z"),
            SSA,
        ],
    },
    {
        # Normal: house down payment to a title company he already paid earnest money to.
        "accountId": "acc-1002",
        "clientName": "David Okafor",
        "clientAge": 41,
        "accountOpened": "2015-08-20",
        "balance": 212500,
        "advisor": {"contactId": "adv-02", "name": "Priya Natarajan"},
        "emergencyContact": {"contactId": "ec-02", "name": "Grace Okafor", "relationship": "spouse"},
        "jointOwners": [],
        "knownPayees": [
            payee("pay-200", "Summit National Bank checking", "bank", "2015-08-20T00:00:00Z"),
            payee("pay-201", "Northwind Corp payroll", "bank", "2019-02-01T00:00:00Z"),
            payee("pay-202", "Lakeside Title & Escrow", "bank", "2026-09-02T15:30:00Z"),
        ],
    },
    {
        # Normal: a 66-year-old's usual monthly transfer. Senior, but nothing else unusual.
        "accountId": "acc-1003",
        "clientName": "Linda Park",
        "clientAge": 66,
        "accountOpened": "2009-11-02",
        "balance": 348000,
        "advisor": {"contactId": "adv-01", "name": "Daniel Reyes"},
        "emergencyContact": {"contactId": "ec-03", "name": "Brian Park", "relationship": "son"},
        "jointOwners": [],
        "knownPayees": [
            payee("pay-300", "Cedar Credit Union checking", "bank", "2009-11-02T00:00:00Z"),
            SSA,
        ],
    },
    {
        # Normal: small withdrawal to his own checking account.
        "accountId": "acc-1004",
        "clientName": "Marcus Bell",
        "clientAge": 34,
        "accountOpened": "2020-01-14",
        "balance": 41200,
        "advisor": {"contactId": "adv-02", "name": "Priya Natarajan"},
        "emergencyContact": {"contactId": "ec-04", "name": "Tanya Bell", "relationship": "sister"},
        "jointOwners": [],
        "knownPayees": [
            payee("pay-400", "Riverbend Bank checking", "bank", "2020-01-14T00:00:00Z"),
        ],
    },
    {
        # Joint owner is the scammer: nephew Kevin moves money to a new "consulting" payee by phone.
        # Claude should put jo-05 in doNotNotify so Kevin never hears about the hold.
        "accountId": "acc-1005",
        "clientName": "Harold Brooks",
        "clientAge": 81,
        "accountOpened": "1998-05-11",
        "balance": 112000,
        "advisor": {"contactId": "adv-03", "name": "Monica Alvarez"},
        "emergencyContact": {"contactId": "ec-05", "name": "Rita Brooks", "relationship": "sister"},
        "jointOwners": [{"contactId": "jo-05", "name": "Kevin Brooks", "relationship": "nephew"}],
        "knownPayees": [
            payee("pay-500", "Granite State Bank checking", "bank", "2002-03-01T00:00:00Z"),
            SSA,
        ],
    },
    {
        # No advisor: romance scam. She gets the scam-check chat instead of an advisor call.
        "accountId": "acc-1006",
        "clientName": "Dorothy Nguyen",
        "clientAge": 72,
        "accountOpened": "2012-07-09",
        "balance": 64000,
        "advisor": None,
        "emergencyContact": {"contactId": "ec-06", "name": "Alan Nguyen", "relationship": "son"},
        "jointOwners": [],
        "knownPayees": [
            payee("pay-600", "Harborview Bank checking", "bank", "2012-07-09T00:00:00Z"),
            payee("pay-601", "Midstate Teachers Pension", "bank", "2014-06-30T00:00:00Z"),
        ],
    },
]

SCENARIOS = [
    {
        "accountId": "acc-1001",
        "story": "Hero. A 'bank security officer' called and told her to move everything to a safe account.",
        "expectedLevel": "high",
        "request": {
            "amount": 180000,
            "payee": {"name": "CoinVault Exchange", "type": "crypto_exchange", "addedAt": "2026-10-02T12:01:00Z"},
            "channel": "web",
            "clientNote": "Moving funds to a safe account as instructed by bank security.",
        },
    },
    {
        "accountId": "acc-1002",
        "story": "Closing on a house. Same title company he paid earnest money to last month.",
        "expectedLevel": "low",
        "request": {
            "amount": 60000,
            "payee": {"name": "Lakeside Title & Escrow", "type": "bank", "addedAt": "2026-09-02T15:30:00Z"},
            "channel": "web",
            "clientNote": "Down payment for closing on 412 Alder St.",
        },
    },
    {
        "accountId": "acc-1003",
        "story": "Her usual monthly transfer to her own credit union.",
        "expectedLevel": "low",
        "request": {
            "amount": 3000,
            "payee": {"name": "Cedar Credit Union checking", "type": "bank", "addedAt": "2009-11-02T00:00:00Z"},
            "channel": "web",
            "clientNote": "",
        },
    },
    {
        "accountId": "acc-1004",
        "story": "Small withdrawal to his own checking account.",
        "expectedLevel": "low",
        "request": {
            "amount": 600,
            "payee": {"name": "Riverbend Bank checking", "type": "bank", "addedAt": "2020-01-14T00:00:00Z"},
            "channel": "web",
            "clientNote": "",
        },
    },
    {
        "accountId": "acc-1005",
        "story": "Joint owner (nephew) phones in a large transfer to a brand-new payee in his own name.",
        "expectedLevel": "high",
        "request": {
            "amount": 95000,
            "payee": {"name": "K. Brooks Consulting LLC", "type": "individual", "addedAt": "2026-10-02T09:40:00Z"},
            "channel": "phone",
            "clientNote": "Kevin Brooks calling for my uncle. He wants to invest with my company.",
        },
    },
    {
        "accountId": "acc-1006",
        "story": "Romance scam, no advisor. An online friend overseas needs 'customs fees'.",
        "expectedLevel": "high",
        "request": {
            "amount": 25000,
            "payee": {"name": "James Whitfield", "type": "individual", "addedAt": "2026-10-01T22:15:00Z"},
            "channel": "web",
            "clientNote": "Helping a friend pay customs fees so his shipment can be released.",
        },
    },
]


def iso(day, hour, minute=0):
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def history_days():
    start = HISTORY_END - timedelta(days=HISTORY_DAYS - 1)
    return [start + timedelta(days=i) for i in range(HISTORY_DAYS)]


def monthly(day_of_month):
    return [d for d in history_days() if d.day == day_of_month]


def known(account, payee_id):
    return next(p for p in account["knownPayees"] if p["payeeId"] == payee_id)


def build_history(account):
    """Return (day, hour, type, amount, payeeId, channel) rows for one account."""
    acc = account["accountId"]
    rows = []
    if acc == "acc-1001":
        rows += [(d, 13, "deposit", 2140, "pay-001", "branch") for d in monthly(3)]
        rows += [(d, 15, "transfer", 1500, "pay-100", "phone") for d in monthly(5)]
        rows += [(d, 16, "withdrawal", rng.choice([200, 250, 300]), "pay-100", "branch") for d in monthly(20)]
    elif acc == "acc-1002":
        fridays = [d for d in history_days() if d.weekday() == 4][::2]
        rows += [(d, 14, "deposit", 1200, "pay-201", "web") for d in fridays]
        rows += [(date(2026, 9, 10), 17, "transfer", 5000, "pay-202", "web")]  # earnest money
        rows += [(d, 18, "transfer", 750, "pay-200", "web") for d in monthly(15)]
    elif acc == "acc-1003":
        rows += [(d, 14, "transfer", 3000, "pay-300", "web") for d in monthly(1)]
        rows += [(d, 13, "deposit", 2480, "pay-001", "web") for d in monthly(3)]
    elif acc == "acc-1004":
        rows += [(d, 15, "deposit", 500, "pay-400", "web") for d in monthly(1)]
        for d in history_days():
            if rng.random() < 0.06:
                rows.append((d, rng.randint(14, 22), "withdrawal", rng.choice([150, 200, 300, 450, 600]), "pay-400", "web"))
    elif acc == "acc-1005":
        rows += [(d, 13, "deposit", 1960, "pay-001", "branch") for d in monthly(3)]
        rows += [(d, 15, "transfer", 1200, "pay-500", "branch") for d in monthly(10)]
    elif acc == "acc-1006":
        rows += [(d, 14, "deposit", 1850, "pay-601", "web") for d in monthly(1)]
        rows += [(d, 16, "transfer", 900, "pay-600", "web") for d in monthly(6)]

    # Everyday activity for every account: a monthly dividend and a few small withdrawals to their own checking.
    checking = account["knownPayees"][0]["payeeId"]
    channels = ["branch", "phone"] if account["clientAge"] >= 75 else ["web"]
    rows += [(d, 12, "deposit", round(account["balance"] * 0.0025), checking, "web") for d in monthly(25)]
    for d in history_days():
        if rng.random() < 0.08:
            rows.append((d, rng.randint(14, 21), "withdrawal", rng.choice([100, 150, 200, 300]), checking, rng.choice(channels)))
    return rows


def main():
    transactions = []
    n = 1
    for account in ACCOUNTS:
        used = set()
        for day, hour, type_, amount, payee_id, channel in sorted(build_history(account), key=lambda r: (r[0], r[1])):
            minute = rng.randint(0, 59)
            while iso(day, hour, minute) in used:  # (accountId, timestamp) is the table key
                minute = (minute + 1) % 60
            timestamp = iso(day, hour, minute)
            used.add(timestamp)
            transactions.append({
                "transactionId": f"txn-{n:04d}",
                "accountId": account["accountId"],
                "timestamp": timestamp,
                "type": type_,
                "amount": amount,
                "payee": known(account, payee_id),
                "channel": channel,
                "clientNote": "",
            })
            n += 1

    scenarios = [
        {"scenarioId": f"scn-{i}", **{k: v for k, v in s.items() if k != "request"},
         "request": {"accountId": s["accountId"], **s["request"]}}
        for i, s in enumerate(SCENARIOS, start=1)
    ]

    DATA_DIR.mkdir(exist_ok=True)
    for name, rows in (("accounts", ACCOUNTS), ("transactions", transactions), ("scenarios", scenarios)):
        (DATA_DIR / f"{name}.json").write_text(json.dumps(rows, indent=2) + "\n")
    print(f"{len(ACCOUNTS)} accounts, {len(transactions)} transactions, {len(scenarios)} scenarios -> {DATA_DIR}")


if __name__ == "__main__":
    main()
