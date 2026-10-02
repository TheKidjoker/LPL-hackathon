"""Rule-based risk signals, computed before Claude is called. Owner: Thomas."""


def compute_signals(account, transaction, history):
    """Return a list of {"name", "detail"} for every rule that fires.

    Rules to build: new_payee, full_liquidation, senior_client (age 65 or older),
    first_crypto, unusual_timing, payee_added_recently (within 24 hours).
    """
    # TODO(Thomas): implement the rules above
    return []
