"""The hero Case from docs/api.md. Stub handlers return this until db.py is real.

Delete each use as the real code lands. frontend/src/mock/sampleCase.js holds the same data.
"""

import copy

SAMPLE_CASE = {
    "caseId": "case-0001",
    "accountId": "acc-1001",
    "clientName": "Margaret Ellis",
    "createdAt": "2026-10-02T14:05:00Z",
    "status": "HELD",
    "transaction": {
        "transactionId": "txn-9001",
        "accountId": "acc-1001",
        "timestamp": "2026-10-02T14:05:00Z",
        "type": "withdrawal",
        "amount": 180000,
        "payee": {
            "payeeId": "pay-777",
            "name": "CoinVault Exchange",
            "type": "crypto_exchange",
            "addedAt": "2026-10-02T12:01:00Z",
        },
        "channel": "web",
        "clientNote": "Moving funds to a safe account as instructed by bank security.",
    },
    "risk": {
        "score": 92,
        "level": "high",
        "signals": [
            {"name": "new_payee", "detail": "Payee added 2 hours before the request"},
            {"name": "full_liquidation", "detail": "Withdrawal is 100% of the account balance"},
            {"name": "senior_client", "detail": "Client is 78"},
            {"name": "first_crypto", "detail": "No crypto activity in 22 years"},
        ],
        "memo": (
            "Margaret Ellis, 78, asked to send her full $180,000 balance to CoinVault Exchange, "
            "a crypto payee added two hours earlier. She has had no crypto activity in 22 years, "
            "and her note repeats a common impostor script about moving money to a 'safe account'. "
            "This matches an authorized-push scam. Recommend a temporary hold under FINRA Rule 2165 "
            "and proposed Rule 2166 while the client and her emergency contact are reached."
        ),
        "doNotNotify": [],
    },
    "holdEndsAt": "2026-10-16",
    "notified": ["client", "adv-01", "fraud-team"],
    "responses": [],
    "decision": None,
    "audit": [
        {"timestamp": "2026-10-02T14:05:07Z", "actor": "system", "action": "HELD", "detail": "Risk score 92"}
    ],
}


def sample_case():
    return copy.deepcopy(SAMPLE_CASE)
