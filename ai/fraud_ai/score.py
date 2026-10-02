"""score_withdrawal: rule signals plus Claude's score and memo. Owner: Thomas.

Stub: returns the sample Risk from docs/api.md so handlers can be built now.
Replace the body with: compute_signals, fill prompts/memo.txt, converse_json,
validate the keys and ranges, return the dict.
"""

import copy

SAMPLE_RISK = {
    "score": 92,
    "level": "high",
    "signals": [
        {"name": "new_payee", "detail": "Payee added 2 hours before the request"},
        {"name": "full_liquidation", "detail": "Withdrawal is 100% of the account balance"},
        {"name": "senior_client", "detail": "Client is 78"},
        {"name": "first_crypto", "detail": "No crypto activity in 22 years"},
    ],
    "memo": "Stub memo. The real memo comes from Claude once score.py is built.",
    "doNotNotify": [],
}


def score_withdrawal(account, transaction, history):
    """Return {"score", "level", "signals", "memo", "doNotNotify"} as in docs/api.md."""
    # TODO(Thomas): real implementation
    return copy.deepcopy(SAMPLE_RISK)
