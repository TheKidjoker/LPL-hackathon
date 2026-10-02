"""score_withdrawal: rule signals plus Claude's score and memo. Owner: Thomas.

Raises on any Claude failure. The handler owns the manual-review fallback
(docs/api.md), and can build it with fallback_risk(compute_signals(...)).
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from string import Template

from fraud_ai import bedrock_client
from fraud_ai.signals import compute_signals

PROMPT = Template((Path(__file__).parent / "prompts" / "memo.txt").read_text(encoding="utf-8"))
HISTORY_DAYS = 90
MAX_HISTORY_ROWS = 40
MAX_CLAUDE_SIGNALS = 4  # keeps the fraud view readable; Claude lists its strongest first
FALLBACK_MEMO = "Automated review unavailable. Held for manual review."


def level_for(score):
    if score is None:
        return "unknown"
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def fallback_risk(signals):
    """The api.md manual-review Risk, for when Claude fails."""
    return {"score": None, "level": "unknown", "signals": list(signals or []), "memo": FALLBACK_MEMO, "doNotNotify": []}


def _contacts(account):
    contacts = list(account.get("jointOwners") or [])
    if account.get("emergencyContact"):
        contacts.append(account["emergencyContact"])
    return [c for c in contacts if c and c.get("contactId")]


def _account_summary(account):
    # Only what matters for risk: no account numbers, no addresses.
    advisor = account.get("advisor")
    return {
        "clientName": account.get("clientName"),
        "clientAge": account.get("clientAge"),
        "accountOpened": account.get("accountOpened"),
        "balance": account.get("balance"),
        "hasAdvisor": bool(advisor),
        "knownPayees": [
            {"name": p.get("name"), "type": p.get("type"), "addedAt": p.get("addedAt")}
            for p in account.get("knownPayees") or []
        ],
    }


def _recent_history(history, transaction):
    now = _parse(transaction.get("timestamp")) or datetime.now().astimezone()
    cutoff = now - timedelta(days=HISTORY_DAYS)
    rows = []
    for t in history or []:
        ts = _parse(t.get("timestamp"))
        if ts and ts < cutoff:
            continue
        payee = t.get("payee") or {}
        rows.append({
            "timestamp": t.get("timestamp"),
            "type": t.get("type"),
            "amount": t.get("amount"),
            "payee": payee.get("name"),
            "payeeType": payee.get("type"),
        })
    rows.sort(key=lambda r: r["timestamp"] or "", reverse=True)
    return rows[:MAX_HISTORY_ROWS]


def _parse(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def build_prompt(account, transaction, history, signals):
    txn = {k: v for k, v in transaction.items() if k != "clientNote"}
    contacts = [
        {"contactId": c["contactId"], "name": c.get("name"), "relationship": c.get("relationship")}
        for c in _contacts(account)
    ]
    dump = lambda obj: json.dumps(obj, indent=1, default=str)
    return PROMPT.safe_substitute(
        account=dump(_account_summary(account)),
        transaction=dump(txn),
        history=dump(_recent_history(history, transaction)) if history else "(no transactions in the last 90 days)",
        signals=dump(signals) if signals else "(none fired)",
        client_note=transaction.get("clientNote") or "(none)",
        advisor_note="(none yet)",
        contacts=dump(contacts) if contacts else "(none on file)",
    )


def validate(raw, account, rule_signals):
    """Turn Claude's JSON into the exact Risk shape, or raise ValueError."""
    if not isinstance(raw, dict):
        raise ValueError("Claude's answer is not a JSON object")
    try:
        score = int(round(float(raw.get("score"))))
    except (TypeError, ValueError):
        raise ValueError(f"Bad score from Claude: {raw.get('score')!r}")
    score = max(0, min(100, score))

    memo = raw.get("memo")
    if not isinstance(memo, str) or not memo.strip():
        raise ValueError("Claude returned an empty memo")

    signals = [dict(s) for s in rule_signals]
    seen = {s["name"] for s in signals}
    for s in (raw.get("signals") or [])[:MAX_CLAUDE_SIGNALS]:
        if isinstance(s, dict) and isinstance(s.get("name"), str) and s["name"] not in seen:
            signals.append({"name": s["name"], "detail": str(s.get("detail") or "")})
            seen.add(s["name"])

    allowed = {c["contactId"] for c in _contacts(account)}
    do_not_notify = [c for c in raw.get("doNotNotify") or [] if c in allowed]

    return {
        "score": score,
        "level": level_for(score),  # derived from the score so it always matches the hold threshold
        "signals": signals,
        "memo": memo.strip(),
        "doNotNotify": sorted(set(do_not_notify), key=do_not_notify.index),
    }


def score_withdrawal(account, transaction, history):
    """Return {"score", "level", "signals", "memo", "doNotNotify"} as in docs/api.md."""
    account = account or {}
    transaction = transaction or {}
    signals = compute_signals(account, transaction, history)
    raw = bedrock_client.converse_json(build_prompt(account, transaction, history, signals), max_tokens=2000)
    return validate(raw, account, signals)
