"""Hold expiry, run every 15 minutes by EventBridge Scheduler. Owner: Thomas.

Finds held cases whose hold has passed its end date (5:00 PM Eastern on holdEndsAt) with no
fraud-team decision, and escalates them. It never releases: money a scam may be targeting
only leaves after a person decides. Not an API endpoint.

For a demo or a test, invoke it with {"asOf": "2026-10-17T12:00:00Z"} to act as if that time
has come. The firm's real policy at hold expiry belongs to compliance; escalation is the safe
default.
"""

import logging
from datetime import datetime, timezone

from common import audit, case_state, db

logger = logging.getLogger()

OPEN_HOLDS = (case_state.HELD, case_state.EXTENDED)
# holdEndsAt is a date; a hold ends at 5:00 PM Eastern that day (21:00 UTC during daylight time).
HOLD_ENDS_AT_UTC = "T21:00:00Z"


def _now(event):
    as_of = (event or {}).get("asOf")
    if as_of:
        return datetime.fromisoformat(as_of.replace("Z", "+00:00"))
    return datetime.now(timezone.utc)


def expired(case, now):
    ends = case.get("holdEndsAt")
    if not ends:
        return False
    return now >= datetime.fromisoformat((ends + HOLD_ENDS_AT_UTC).replace("Z", "+00:00"))


def handler(event, context):
    now = _now(event)
    escalated = []
    for status in OPEN_HOLDS:
        for case in db.list_cases_by_status(status):
            if not expired(case, now):
                continue
            # Re-read, so a fraud-team decision made a moment ago wins.
            fresh = db.get_case(case["caseId"])
            if not fresh or fresh.get("status") not in OPEN_HOLDS or not expired(fresh, now):
                continue
            db.update_case(fresh["caseId"], {"status": case_state.ESCALATED})
            audit.write_audit(
                fresh["caseId"], "system", case_state.ESCALATED,
                f"Hold reached its end date ({fresh['holdEndsAt']}) with no decision. Escalated so the funds stay protected until the fraud team decides",
            )
            escalated.append(fresh["caseId"])
    logger.info("Hold expiry check at %s: escalated %s", now.isoformat(), escalated)
    return {"checkedAt": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "escalated": escalated}
