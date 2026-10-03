"""Generate the seed data in data/. Owner: Kaylin (contact history and pre-seeded cases added by Thomas).

    python scripts/make_seed_data.py

Edit the accounts and history rules here, then re-run. Output is the same every run (fixed random seed).
Shapes are in docs/api.md. All names and numbers are fake.

- accounts.json      ten Accounts: the six demo scenarios plus four with a case already in the queue. Each has
                     a contactLog (calls, emails, chats with the firm) and advisorNotes (the advisor's CRM notes)
- transactions.json  90 days of normal history for every account, ending the day before the demo
- scenarios.json     the POST /withdrawals request for each demo scenario, with the expected level
- cases.json         four pre-seeded Cases in every state: HELD, EXTENDED, ESCALATED, RELEASED
- audit.json         the audit rows for those Cases
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

PRESEED_ACCOUNTS = [
    # Accounts that already have a case in the queue when the demo starts (cases.json).
    {
        "accountId": "acc-1007",
        "clientName": "Eleanor Whitfield",
        "clientAge": 84,
        "accountOpened": "1996-04-22",
        "balance": 96000,
        "advisor": {"contactId": "adv-01", "name": "Daniel Reyes"},
        "emergencyContact": {"contactId": "ec-07", "name": "Martha Whitfield", "relationship": "daughter"},
        "jointOwners": [],
        "knownPayees": [payee("pay-700", "Old Mill Savings checking", "bank", "2001-02-12T00:00:00Z"), SSA],
    },
    {
        "accountId": "acc-1008",
        "clientName": "Robert Castillo",
        "clientAge": 69,
        "accountOpened": "2008-10-06",
        "balance": 233000,
        "advisor": {"contactId": "adv-03", "name": "Monica Alvarez"},
        "emergencyContact": {"contactId": "ec-08", "name": "Diane Castillo", "relationship": "spouse"},
        "jointOwners": [],
        "knownPayees": [payee("pay-800", "Desert Federal Credit Union checking", "bank", "2008-10-06T00:00:00Z"), SSA],
    },
    {
        "accountId": "acc-1009",
        "clientName": "Janet Moore",
        "clientAge": 58,
        "accountOpened": "2013-05-17",
        "balance": 151000,
        "advisor": {"contactId": "adv-02", "name": "Priya Natarajan"},
        "emergencyContact": {"contactId": "ec-09", "name": "Paul Moore", "relationship": "brother"},
        "jointOwners": [],
        "knownPayees": [payee("pay-900", "Lakeshore Bank checking", "bank", "2013-05-17T00:00:00Z")],
    },
    {
        "accountId": "acc-1010",
        "clientName": "Walter Price",
        "clientAge": 91,
        "accountOpened": "1989-09-01",
        "balance": 74000,
        "advisor": {"contactId": "adv-03", "name": "Monica Alvarez"},
        "emergencyContact": {"contactId": "ec-10", "name": "Carol Price", "relationship": "daughter"},
        "jointOwners": [],
        "knownPayees": [payee("pay-1000", "Granite State Bank checking", "bank", "1995-03-01T00:00:00Z"), SSA],
    },
]

# What the firm already knew before each withdrawal: calls, emails, and chats with the client or
# someone acting for them, plus the advisor's CRM notes. Firm records, written by employees; quoted
# words are what the caller said and are evidence, never instructions.
CONTACT_LOG = {
    "acc-1001": [
        ("2026-09-29T15:10:00Z", "phone", "client", "Margaret Ellis",
         "Called Investor Support asking how fast a wire can go out and whether wires can go to \"a crypto account.\" Sounded rushed and said she \"can't talk about it right now.\""),
        ("2026-10-01T14:02:00Z", "phone", "client", "Margaret Ellis",
         "Asked to raise her online daily transfer limit. Said \"the bank security department\" is helping her protect her money. Rep suggested calling her advisor; she declined."),
    ],
    "acc-1002": [
        ("2026-09-30T16:20:00Z", "phone", "advisor", "Priya Natarajan",
         "Outbound call. David confirmed closing on 412 Alder St. is set for early October with Lakeside Title & Escrow. Advisor verified the wire instructions by calling Lakeside at the number on the purchase contract."),
    ],
    "acc-1003": [],
    "acc-1004": [],
    "acc-1005": [
        ("2026-09-18T17:40:00Z", "phone", "third_party", "Kevin Brooks (joint owner, nephew)",
         "Asked to have Harold's statements sent to his own email and to be listed as the primary contact. Told only Harold can request that."),
        ("2026-09-27T15:05:00Z", "phone", "third_party", "Kevin Brooks (joint owner, nephew)",
         "Asked how much can be withdrawn same-day and whether Harold \"needs to be on the call.\" Mentioned \"an investment opportunity\" for his business."),
    ],
    "acc-1006": [
        ("2026-09-12T19:30:00Z", "web_chat", "client", "Dorothy Nguyen",
         "Asked how to buy Bitcoin and whether she can send it \"to a friend overseas who is stuck in customs.\""),
        ("2026-09-26T18:15:00Z", "phone", "client", "Dorothy Nguyen",
         "Asked if the firm can \"release a package from customs\" for a man she met online. Rep explained the firm doesn't handle customs and flagged a possible romance scam. No advisor on the account to escalate to."),
    ],
    "acc-1007": [
        ("2026-09-30T13:50:00Z", "phone", "client", "Eleanor Whitfield",
         "Asked to withdraw cash and buy gift cards \"for my grandson's bail.\" Said a lawyer told her not to tell her family."),
    ],
    "acc-1008": [
        ("2026-09-25T15:00:00Z", "branch", "client", "Robert Castillo",
         "Visited the branch with his wife to ask about paying for an RV. Showed a purchase agreement from Coastal RV Sales."),
    ],
    "acc-1009": [
        ("2026-09-22T14:45:00Z", "email", "client", "Janet Moore",
         "Emailed asking how to wire money to \"Pacific Asset Recovery Group,\" who say they can recover $40,000 she lost in a crypto scam last year for an upfront fee."),
        ("2026-09-29T16:30:00Z", "phone", "client", "Janet Moore",
         "Called to say the recovery firm needs the fee \"by Friday or the funds are forfeited.\""),
    ],
    "acc-1010": [
        ("2026-10-02T13:20:00Z", "phone", "third_party", "Caller saying he is from \"Microsoft support\"",
         "A man claiming to be from Microsoft support called asking for Walter's account number \"to process a refund.\" Rep refused and ended the call."),
    ],
}

ADVISOR_NOTES = {
    "acc-1001": [("2026-08-14T15:00:00Z", "Daniel Reyes",
                  "Annual review. Margaret was widowed in March; her daughter Susan helps with bills. Conservative, income-focused. Has never shown interest in crypto.")],
    "acc-1002": [("2026-09-02T16:00:00Z", "Priya Natarajan",
                  "Buying his first home. Earnest money to Lakeside Title & Escrow goes out Sept 10; the down payment follows at closing in early October.")],
    "acc-1003": [("2026-07-10T14:00:00Z", "Daniel Reyes",
                  "Retired in 2021. Moves $3,000 a month to her credit union for living expenses.")],
    "acc-1004": [("2026-06-05T18:00:00Z", "Priya Natarajan", "Self-directed, prefers the web app. Small, frequent withdrawals are normal for him.")],
    "acc-1005": [("2026-07-22T15:30:00Z", "Monica Alvarez",
                  "Harold had a fall in June. His nephew Kevin moved in to help and was added as a joint owner on June 30 at Harold's request. Harold seemed less engaged than usual on our call.")],
    "acc-1006": [],
    "acc-1007": [("2026-05-03T14:00:00Z", "Daniel Reyes", "Lives alone. Very close to her grandchildren. Asked us to always call her daughter Martha if anything seems off.")],
    "acc-1008": [("2026-09-24T17:00:00Z", "Monica Alvarez", "Robert and Diane plan to buy an RV for retirement travel, around $50,000. Expect a large payment to the dealer this month.")],
    "acc-1009": [("2026-03-11T15:00:00Z", "Priya Natarajan", "Janet lost about $40,000 to a crypto investment scam in 2025. Very motivated to get it back.")],
    "acc-1010": [],
}

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


def contact_log(account_id):
    return [{"at": at, "channel": channel, "party": party, "who": who, "summary": summary}
            for at, channel, party, who, summary in CONTACT_LOG.get(account_id, [])]


def advisor_notes(account_id):
    return [{"at": at, "by": by, "text": text} for at, by, text in ADVISOR_NOTES.get(account_id, [])]


def preseed_cases():
    """Cases already in the queue when the demo starts, in every state a reviewer meets.

    Returns (cases, audit rows). Memos read like Juno's; signals follow ai/fraud_ai/signals.py.
    """
    def case(case_id, account, created, status, amount, payee_, channel, note, score, signals, memo,
             hold_ends, notified, responses, decision, audit, do_not_notify=()):
        return {
            "caseId": case_id, "accountId": account["accountId"], "clientName": account["clientName"],
            "createdAt": created, "status": status,
            "transaction": {"transactionId": f"txn-{case_id[5:]}", "accountId": account["accountId"], "timestamp": created,
                            "type": "withdrawal", "amount": amount, "payee": payee_, "channel": channel, "clientNote": note},
            "risk": {"score": score, "level": "high" if score >= 70 else "medium" if score >= 40 else "low",
                     "signals": [{"name": n, "detail": d} for n, d in signals], "memo": memo, "doNotNotify": list(do_not_notify)},
            "holdEndsAt": hold_ends, "notified": notified, "responses": responses, "decision": decision,
        }, [{"caseId": case_id, "timestamp": ts, "actor": actor, "action": action, "detail": detail}
            for ts, actor, action, detail in audit]

    acc = {a["accountId"]: a for a in PRESEED_ACCOUNTS}
    rows = [
        case("case-seed-07", acc["acc-1007"], "2026-09-30T14:05:00Z", "ESCALATED", 62000,
             payee("pay-701", "QuickCard Gift Card Wholesale", "individual", "2026-09-30T13:55:00Z"), "phone",
             "Grandson needs bail money today. Lawyer said not to tell family.", 97,
             [("new_payee", "QuickCard Gift Card Wholesale has never been paid from this account"),
              ("payee_added_recently", "Payee added 0 hours before the request"),
              ("senior_client", "Client is 84"),
              ("large_vs_history", "52x the largest past withdrawal ($1,200)"),
              ("grandparent_scam_script", "Note repeats the 'grandchild in jail, don't tell family' script"),
              ("secrecy_instruction", "Client was told to keep it from her family")],
             "Eleanor Whitfield, 84, asked to send $62,000 to a gift-card wholesaler added minutes earlier, saying her grandson needs bail and a lawyer told her not to tell her family. This is the classic grandparent scam: urgency, secrecy, and an untraceable payment method. Her daughter Martha confirmed the grandson is home and safe. Recommend keeping the hold under FINRA Rule 2165 and referring to Adult Protective Services.",
             "2026-10-14", ["client", "fraud-team", "adv-01", "ec-07"],
             [{"responseId": "resp-s07a", "role": "client", "kind": "deny", "text": "After talking to my daughter I don't want this to go through.", "at": "2026-09-30T18:40:00Z"},
              {"responseId": "resp-s07b", "role": "advisor", "kind": "note", "text": "Called Martha (daughter). Grandson is home and safe. Eleanor is upset but relieved. Classic grandparent scam.", "at": "2026-09-30T17:10:00Z"}],
             {"action": "escalate", "by": "fraud", "at": "2026-09-30T19:02:00Z", "note": "Grandparent scam confirmed by family. Referred to investigations and APS."},
             [("2026-09-30T14:05:01.000Z", "system", "RECEIVED", "Held while automated review runs"),
              ("2026-09-30T14:05:12.000Z", "system", "HELD", "Risk score 97"),
              ("2026-09-30T17:10:00.000Z", "advisor", "NOTE", "Called Martha (daughter). Grandson is home and safe."),
              ("2026-09-30T18:40:00.000Z", "client", "DENY", "After talking to my daughter I don't want this to go through."),
              ("2026-09-30T19:02:00.000Z", "fraud", "ESCALATED", "Grandparent scam confirmed by family. Referred to investigations and APS.")]),
        case("case-seed-08", acc["acc-1008"], "2026-09-29T16:20:00Z", "RELEASED", 48500,
             payee("pay-801", "Coastal RV Sales", "individual", "2026-09-29T16:00:00Z"), "web",
             "Down payment on our RV", 72,
             [("new_payee", "Coastal RV Sales has never been paid from this account"),
              ("payee_added_recently", "Payee added 0 hours before the request"),
              ("senior_client", "Client is 69"),
              ("large_vs_history", "21x the largest past withdrawal ($2,300)")],
             "Robert Castillo, 69, asked to send $48,500 to Coastal RV Sales, a payee added 20 minutes earlier. The amount is far above his usual withdrawals. However, his advisor's notes and a branch visit with his wife show a planned RV purchase with a signed agreement. Recommend a short hold and callback to confirm before release.",
             None, ["client", "fraud-team", "adv-03", "ec-08"],
             [{"responseId": "resp-s08a", "role": "client", "kind": "confirm", "text": "Yes, it's for our RV.", "at": "2026-09-29T16:45:00Z"},
              {"responseId": "resp-s08b", "role": "advisor", "kind": "note", "text": "Confirmed with Robert and Diane by phone on the number of record. Dealer verified independently.", "at": "2026-09-29T17:30:00Z"}],
             {"action": "release", "by": "fraud", "at": "2026-09-29T18:05:00Z", "note": "Verified by callback on the number of record and with the dealer. Legitimate RV purchase."},
             [("2026-09-29T16:20:01.000Z", "system", "RECEIVED", "Held while automated review runs"),
              ("2026-09-29T16:20:11.000Z", "system", "HELD", "Risk score 72"),
              ("2026-09-29T16:45:00.000Z", "client", "CONFIRM", "Yes, it's for our RV."),
              ("2026-09-29T17:30:00.000Z", "advisor", "NOTE", "Confirmed by phone on the number of record. Dealer verified."),
              ("2026-09-29T18:05:00.000Z", "fraud", "RELEASED", "Verified by callback and with the dealer. Legitimate RV purchase.")]),
        case("case-seed-09", acc["acc-1009"], "2026-10-01T15:10:00Z", "EXTENDED", 18000,
             payee("pay-901", "Pacific Asset Recovery Group", "individual", "2026-10-01T14:50:00Z"), "web",
             "Fee to recover my lost crypto", 91,
             [("new_payee", "Pacific Asset Recovery Group has never been paid from this account"),
              ("payee_added_recently", "Payee added 0 hours before the request"),
              ("large_vs_history", "12x the largest past withdrawal ($1,500)"),
              ("recovery_scam_pattern", "Upfront fee to 'recover' money lost in an earlier scam"),
              ("deadline_pressure", "Told the fee is due 'by Friday or the funds are forfeited'")],
             "Janet Moore, 58, asked to send an $18,000 'fee' to Pacific Asset Recovery Group, who claim they can recover the $40,000 she lost in a crypto scam last year. Upfront-fee recovery offers aimed at past victims are a known follow-on scam, and the deadline pressure fits. She is under 65, so this delay relies on the firm's fraud policy; proposed FINRA Rule 2166 would cover it. Recommend extending while investigations verifies the company.",
             "2026-10-22", ["client", "fraud-team", "adv-02", "ec-09"],
             [{"responseId": "resp-s09a", "role": "client", "kind": "confirm", "text": "Yes I sent it, they are getting my money back.", "at": "2026-10-01T16:00:00Z"},
              {"responseId": "resp-s09b", "role": "advisor", "kind": "note", "text": "Spoke with Janet. She is convinced it's real. I explained recovery scams; she wants to wait for the firm's review.", "at": "2026-10-01T18:20:00Z"}],
             {"action": "extend", "by": "fraud", "at": "2026-10-02T13:00:00Z", "note": "Recovery-scam pattern. Extending while investigations checks the company."},
             [("2026-10-01T15:10:01.000Z", "system", "RECEIVED", "Held while automated review runs"),
              ("2026-10-01T15:10:13.000Z", "system", "HELD", "Risk score 91"),
              ("2026-10-01T16:00:00.000Z", "client", "CONFIRM", "Yes I sent it, they are getting my money back."),
              ("2026-10-01T18:20:00.000Z", "advisor", "NOTE", "She is convinced it's real; wants to wait for the review."),
              ("2026-10-02T13:00:00.000Z", "fraud", "EXTENDED", "Recovery-scam pattern. Extending while investigations checks the company (hold now ends 2026-10-22)")]),
        case("case-seed-10", acc["acc-1010"], "2026-10-02T14:40:00Z", "HELD", 30000,
             payee("pay-1001", "TechFix Support Services", "individual", "2026-10-02T14:25:00Z"), "phone",
             "Refund processing for computer support", 94,
             [("new_payee", "TechFix Support Services has never been paid from this account"),
              ("payee_added_recently", "Payee added 0 hours before the request"),
              ("senior_client", "Client is 91"),
              ("large_vs_history", "25x the largest past withdrawal ($1,200)"),
              ("tech_support_scam_pattern", "Payment to 'computer support' for a 'refund' right after a fake Microsoft call")],
             "Walter Price, 91, asked to send $30,000 to TechFix Support Services by phone, 80 minutes after a caller claiming to be Microsoft support tried to get his account number 'to process a refund.' Refund-overpayment tech-support scams follow this pattern exactly. Walter has not answered the in-app question yet. Recommend keeping the hold under FINRA Rule 2165 and reaching his daughter Carol.",
             "2026-10-06", ["client", "fraud-team", "adv-03", "ec-10"], [], None,
             [("2026-10-02T14:40:01.000Z", "system", "RECEIVED", "Held while automated review runs"),
              ("2026-10-02T14:40:12.000Z", "system", "HELD", "Risk score 94")]),
    ]
    return [c for c, _ in rows], [a for _, rows_ in rows for a in rows_]


def main():
    accounts = []
    for account in ACCOUNTS + PRESEED_ACCOUNTS:
        accounts.append({**account, "contactLog": contact_log(account["accountId"]),
                         "advisorNotes": advisor_notes(account["accountId"])})
    cases, audit = preseed_cases()

    transactions = []
    n = 1
    for account in ACCOUNTS + PRESEED_ACCOUNTS:
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
    outputs = (("accounts", accounts), ("transactions", transactions), ("scenarios", scenarios),
               ("cases", cases), ("audit", audit))
    for name, rows in outputs:
        (DATA_DIR / f"{name}.json").write_text(json.dumps(rows, indent=2) + "\n")
    print(f"{len(accounts)} accounts, {len(transactions)} transactions, {len(scenarios)} scenarios, "
          f"{len(cases)} pre-seeded cases, {len(audit)} audit rows -> {DATA_DIR}")


if __name__ == "__main__":
    main()
