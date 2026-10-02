"""Rule-based risk signals, computed before Claude is called. Owner: Thomas.

Pure Python, no AWS calls. Every rule is robust to missing fields: a rule that
cannot be evaluated simply does not fire.
"""

from datetime import datetime

SENIOR_AGE = 65
FULL_LIQUIDATION_SHARE = 0.9
RECENT_PAYEE_HOURS = 24
LARGE_VS_HISTORY_MULTIPLE = 5
NORMAL_HOURS = range(7, 21)  # 7:00 to 20:59


def _parse_time(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _payee_key(payee):
    payee = payee or {}
    return payee.get("payeeId") or (payee.get("name") or "").strip().lower() or None


def _known_payee_keys(account, history):
    keys = set()
    for payee in (account or {}).get("knownPayees") or []:
        keys.add(_payee_key(payee))
        keys.add((payee.get("name") or "").strip().lower() or None)
    for txn in history or []:
        payee = txn.get("payee") or {}
        keys.add(_payee_key(payee))
        keys.add((payee.get("name") or "").strip().lower() or None)
    keys.discard(None)
    return keys


def compute_signals(account, transaction, history):
    """Return a list of {"name", "detail"} for every rule that fires."""
    account = account or {}
    transaction = transaction or {}
    history = history or []
    payee = transaction.get("payee") or {}
    amount = transaction.get("amount") or 0
    signals = []

    def add(name, detail):
        signals.append({"name": name, "detail": detail})

    known = _known_payee_keys(account, history)
    payee_keys = {_payee_key(payee), (payee.get("name") or "").strip().lower() or None} - {None}
    if payee_keys and not (payee_keys & known):
        add("new_payee", f"{payee.get('name') or 'This payee'} has never been paid from this account")

    added_at = _parse_time(payee.get("addedAt"))
    txn_time = _parse_time(transaction.get("timestamp"))
    if added_at and txn_time:
        hours = (txn_time - added_at).total_seconds() / 3600
        if 0 <= hours <= RECENT_PAYEE_HOURS:
            shown = f"{hours:.0f} hours" if hours >= 1 else "less than an hour"
            add("payee_added_recently", f"Payee added {shown} before the request")

    balance = account.get("balance")
    if balance and amount and amount >= FULL_LIQUIDATION_SHARE * balance:
        add("full_liquidation", f"Withdrawal is {amount / balance:.0%} of the account balance")

    age = account.get("clientAge")
    if isinstance(age, (int, float)) and age >= SENIOR_AGE:
        add("senior_client", f"Client is {int(age)}")

    if payee.get("type") == "crypto_exchange":
        past_crypto = any((t.get("payee") or {}).get("type") == "crypto_exchange" for t in history)
        if not past_crypto:
            add("first_crypto", "First transfer to a crypto exchange in the account's history")

    if txn_time and txn_time.hour not in NORMAL_HOURS:
        add("unusual_timing", f"Requested at {txn_time.strftime('%H:%M')}, outside normal hours")

    past = [t.get("amount") or 0 for t in history if t.get("type") in ("withdrawal", "transfer")]
    if past and amount > LARGE_VS_HISTORY_MULTIPLE * max(past):
        add("large_vs_history", f"{amount / max(past):.0f}x the largest past withdrawal (${max(past):,.0f})")

    return signals
