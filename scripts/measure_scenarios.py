"""Run every demo scenario through the live API and report the results. Owner: Kaylin.

    python scripts/measure_scenarios.py                    # one run, table to the terminal
    python scripts/measure_scenarios.py --runs 3 --out docs/RESULTS.md

For each scenario in data/scenarios.json: POST /withdrawals as the client (timed end to end),
then GET /cases/{id} as the fraud team. Reports whether each scam was held and each normal
withdrawal released, the score, the time to a decision and memo, and whether flagged contacts
were left out of the alerts. Each payee keeps its age relative to the scenario's request time,
so "added two hours ago" stays true on any day.

The cases it creates are deleted afterwards unless you pass --keep. Uses real Claude calls.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "backend"), str(ROOT / "scripts")]
os.environ.setdefault("AWS_PROFILE", "lpl-hackathon")
os.environ.setdefault("AWS_REGION", "us-east-1")

SCENARIO_TIME = datetime(2026, 10, 2, 14, 5, tzinfo=timezone.utc)  # when the scenarios' payee ages are measured from
STACK_NAME = "fraud-speed-bump"


def parse_iso(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def api_url():
    import boto3

    stack = boto3.client("cloudformation", region_name=os.environ["AWS_REGION"]).describe_stacks(StackName=STACK_NAME)
    return next(o["OutputValue"] for o in stack["Stacks"][0]["Outputs"] if o["OutputKey"] == "ApiUrl").rstrip("/")


def call(base, role, method, path, body=None):
    request = urllib.request.Request(
        base + path, method=method, data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json", "X-Role": role},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def with_fresh_payee(request):
    """Shift payee.addedAt so the payee is as old now as it was at SCENARIO_TIME."""
    request = json.loads(json.dumps(request))
    added = request["payee"].get("addedAt")
    if added:
        age = SCENARIO_TIME - parse_iso(added)
        request["payee"]["addedAt"] = iso(datetime.now(timezone.utc) - age)
    return request


def run_scenario(base, scenario, account):
    start = time.time()
    status, client_case = call(base, "client", "POST", "/withdrawals", with_fresh_payee(scenario["request"]))
    seconds = time.time() - start
    if status != 201:
        return {"scenario": scenario, "error": f"POST /withdrawals returned {status}: {client_case}", "seconds": seconds}
    _, case = call(base, "fraud", "GET", f"/cases/{client_case['caseId']}")
    stale = case.get("status") != client_case.get("status")
    if stale:  # the read beat the write; read again so the report shows the saved Case
        time.sleep(1)
        _, case = call(base, "fraud", "GET", f"/cases/{client_case['caseId']}")
    risk = case.get("risk") or {}
    expected_hold = scenario["expectedLevel"] == "high"
    held = case.get("status") == "HELD"
    joint = {j["contactId"] for j in account.get("jointOwners") or []}
    return {
        "scenario": scenario,
        "caseId": case["caseId"],
        "seconds": seconds,
        "status": case.get("status"),
        "score": risk.get("score"),
        "level": risk.get("level"),
        "correct": held == expected_hold,
        "expectedHold": expected_hold,
        "doNotNotify": risk.get("doNotNotify") or [],
        "notified": case.get("notified") or [],
        "jointOwnerAlerted": bool(joint & set(case.get("notified") or [])),
        "memo": risk.get("memo") or "",
        "staleRead": stale,
    }


def money(n):
    return f"${n:,.0f}"


def report(results, accounts, runs):
    ok = [r for r in results if "error" not in r]
    scams = [r for r in ok if r["expectedHold"]]
    normal = [r for r in ok if not r["expectedHold"]]
    caught = [r for r in scams if r["status"] == "HELD"]
    false_pos = [r for r in normal if r["status"] == "HELD"]
    secs = sorted(r["seconds"] for r in ok)
    joint_cases = [r for r in ok if accounts[r["scenario"]["accountId"]].get("jointOwners")]

    lines = [
        f"# Scenario results ({datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}, live API, {runs} run{'s' if runs > 1 else ''})",
        "",
        "| Scenario | Client | Amount | Should | Result | Score | Seconds | Correct |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        s = r["scenario"]
        name = accounts[s["accountId"]]["clientName"]
        should = "Hold" if s["expectedLevel"] == "high" else "Release"
        if "error" in r:
            lines.append(f"| {s['scenarioId']} | {name} | {money(s['request']['amount'])} | {should} | ERROR | | {r['seconds']:.1f} | no |")
            continue
        score = "unavailable" if r["score"] is None else f"{r['score']} ({r['level']})"
        lines.append(f"| {s['scenarioId']} | {name} | {money(s['request']['amount'])} | {should} | {r['status']} | {score} | {r['seconds']:.1f} | {'yes' if r['correct'] else 'NO'} |")

    lines += ["", "## Summary", ""]
    lines.append(f"- Scams held: {len(caught)} of {len(scams)}")
    lines.append(f"- Normal withdrawals released: {len(normal) - len(false_pos)} of {len(normal)} (false positives: {len(false_pos)})")
    if secs:
        lines.append(f"- Time to decision and memo: average {sum(secs) / len(secs):.1f}s, slowest {secs[-1]:.1f}s")
    held_dollars = sum(r["scenario"]["request"]["amount"] for r in caught) / runs
    lines.append(f"- Dollars held in scam scenarios: {money(held_dollars)}{' per run' if runs > 1 else ''}")
    if joint_cases:
        lines.append(f"- Joint-owner scam: scammer left out of the alerts in {sum(not r['jointOwnerAlerted'] for r in joint_cases)} of {len(joint_cases)} runs")
    stale = [r for r in ok if r.get("staleRead")]
    if stale:
        lines.append(f"- Stale reads right after submit: {len(stale)} ({', '.join(r['scenario']['scenarioId'] for r in stale)})")
    errors = [r for r in results if "error" in r]
    if errors:
        lines.append(f"- Errors: {len(errors)}")
        lines += [f"  - {r['scenario']['scenarioId']}: {r['error']}" for r in errors]
    return "\n".join(lines) + "\n"


def delete_cases(case_ids):
    from seed_dynamodb import set_table_names_from_stack

    set_table_names_from_stack()
    from common import db

    for case_id in case_ids:
        for row in db.list_audit_rows(case_id):
            db._table(db.AUDIT_TABLE).delete_item(Key={"caseId": case_id, "timestamp": row["timestamp"]})
        db._table(db.CASES_TABLE).delete_item(Key={"caseId": case_id})


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--runs", type=int, default=1, help="run every scenario this many times")
    parser.add_argument("--out", help="also write the report to this file (Markdown)")
    parser.add_argument("--keep", action="store_true", help="keep the cases instead of deleting them")
    args = parser.parse_args()

    accounts = {a["accountId"]: a for a in json.loads((ROOT / "data" / "accounts.json").read_text())}
    scenarios = json.loads((ROOT / "data" / "scenarios.json").read_text())
    base = api_url()

    results = []
    for run in range(args.runs):
        for scenario in scenarios:
            r = run_scenario(base, scenario, accounts[scenario["accountId"]])
            results.append(r)
            print(f"run {run + 1} {scenario['scenarioId']}: {r.get('status', 'ERROR')} {r.get('score', '')} in {r['seconds']:.1f}s"
                  + ("  (stale read, re-read)" if r.get("staleRead") else ""), file=sys.stderr)

    text = report(results, accounts, args.runs)
    print(text)
    if args.out:
        Path(args.out).write_text(text)
    created = [r["caseId"] for r in results if "caseId" in r]
    if created and not args.keep:
        delete_cases(created)
        print(f"Deleted the {len(created)} cases this run created.", file=sys.stderr)


if __name__ == "__main__":
    main()
