"""Run score_withdrawal over every demo scenario in data/ and check the risk level. Live Bedrock calls.

    python ai/eval/run_eval.py
    python ai/eval/run_eval.py --memo      # also print each memo

Scenarios, accounts, and history come from data/ (Kaylin's seed data), so the eval scores
exactly what the demo will. Exits 1 if any scenario lands outside its expected level or
misses an expected doNotNotify.
"""

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent.parent / "data"
sys.path.insert(0, str(HERE.parent))
os.environ.setdefault("AWS_PROFILE", "lpl-hackathon")
os.environ.setdefault("AWS_REGION", "us-east-1")

from fraud_ai import score_withdrawal  # noqa: E402

# The demo withdrawals are submitted at this time, two hours after the hero's payee was added.
REQUESTED_AT = "2026-10-02T14:05:00Z"

# What data/scenarios.json does not record: who Claude should keep out of the alerts.
EXPECT_DO_NOT_NOTIFY = {"acc-1005": ["jo-05"]}


def load_scenarios():
    read = lambda name: json.loads((DATA / name).read_text(encoding="utf-8"))
    accounts = {a["accountId"]: a for a in read("accounts.json")}
    transactions = read("transactions.json")
    cutoff = (datetime.fromisoformat(REQUESTED_AT.replace("Z", "+00:00")) - timedelta(days=90)).strftime("%Y-%m-%dT%H:%M:%SZ")

    scenarios = []
    for s in read("scenarios.json"):
        account_id = s["accountId"]
        history = sorted(
            (t for t in transactions if t["accountId"] == account_id and cutoff <= t["timestamp"] <= REQUESTED_AT),
            key=lambda t: t["timestamp"],
            reverse=True,
        )
        transaction = {
            **s["request"],
            "transactionId": f"txn-eval-{s['scenarioId']}",
            "timestamp": REQUESTED_AT,
            "type": "withdrawal",
        }
        scenarios.append({
            "name": f"{s['scenarioId']} {accounts[account_id]['clientName']}",
            "expected": [s["expectedLevel"]],
            "expectDoNotNotify": EXPECT_DO_NOT_NOTIFY.get(account_id, []),
            "account": accounts[account_id],
            "transaction": transaction,
            "history": history,
        })
    return scenarios


def run(scenario):
    start = time.time()
    try:
        risk = score_withdrawal(scenario["account"], scenario["transaction"], scenario["history"])
        error = None
    except Exception as e:  # report, don't crash the whole eval
        risk, error = None, f"{type(e).__name__}: {e}"
    return scenario, risk, error, time.time() - start


def main():
    scenarios = load_scenarios()
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(run, scenarios))

    failures = 0
    print(f"{'scenario':28} {'expected':9} {'got':8} {'score':>5} {'secs':>5}  doNotNotify")
    for scenario, risk, error, secs in results:
        if error:
            failures += 1
            print(f"{scenario['name']:28} {'/'.join(scenario['expected']):9} ERROR    {'':>5} {secs:5.1f}  {error}")
            continue
        ok = risk["level"] in scenario["expected"] and set(scenario["expectDoNotNotify"]) <= set(risk["doNotNotify"])
        failures += not ok
        mark = "" if ok else "  <-- FAIL"
        print(f"{scenario['name']:28} {'/'.join(scenario['expected']):9} {risk['level']:8} {risk['score']:5} {secs:5.1f}  {risk['doNotNotify']}{mark}")
        if "--memo" in sys.argv:
            print(f"    signals: {[s['name'] for s in risk['signals']]}")
            print(f"    memo: {risk['memo']}\n")

    print(f"\n{len(results) - failures}/{len(results)} passed")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
