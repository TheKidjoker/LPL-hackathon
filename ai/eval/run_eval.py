"""Run score_withdrawal over every scenario and check the risk level. Live Bedrock calls.

    python ai/eval/run_eval.py
    python ai/eval/run_eval.py --memo      # also print each memo

Exits 1 if any scenario lands outside its expected levels or misses an expected doNotNotify.
"""

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
os.environ.setdefault("AWS_PROFILE", "lpl-hackathon")
os.environ.setdefault("AWS_REGION", "us-east-1")

from fraud_ai import score_withdrawal  # noqa: E402


def run(scenario):
    start = time.time()
    try:
        risk = score_withdrawal(scenario["account"], scenario["transaction"], scenario["history"])
        error = None
    except Exception as e:  # report, don't crash the whole eval
        risk, error = None, f"{type(e).__name__}: {e}"
    return scenario, risk, error, time.time() - start


def main():
    scenarios = json.loads((HERE / "scenarios.json").read_text(encoding="utf-8"))
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(run, scenarios))

    failures = 0
    print(f"{'scenario':32} {'expected':14} {'got':8} {'score':>5} {'secs':>5}  doNotNotify")
    for scenario, risk, error, secs in results:
        if error:
            failures += 1
            print(f"{scenario['name']:32} {'/'.join(scenario['expected']):14} ERROR    {'':>5} {secs:5.1f}  {error}")
            continue
        ok = risk["level"] in scenario["expected"] and set(scenario.get("expectDoNotNotify", [])) <= set(risk["doNotNotify"])
        failures += not ok
        mark = "" if ok else "  <-- FAIL"
        print(f"{scenario['name']:32} {'/'.join(scenario['expected']):14} {risk['level']:8} {risk['score']:5} {secs:5.1f}  {risk['doNotNotify']}{mark}")
        if "--memo" in sys.argv:
            print(f"    signals: {[s['name'] for s in risk['signals']]}")
            print(f"    memo: {risk['memo']}\n")

    print(f"\n{len(results) - failures}/{len(results)} passed")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
