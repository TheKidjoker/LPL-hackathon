"""Audit log. Owner: Kaylin. Every change to a Case writes one row."""

from datetime import datetime, timedelta, timezone

from common import db


def _iso_ms(when):
    return when.strftime("%Y-%m-%dT%H:%M:%S.") + f"{when.microsecond // 1000:03d}Z"


def write_audit(case_id, actor, action, detail=""):
    """Write {caseId, timestamp, actor, action, detail} to the Audit table and return the row.

    The timestamp has milliseconds and is the table's sort key, so two rows written in the
    same millisecond would collide. On a collision, move forward 1 ms and try again.
    """
    when = datetime.now(timezone.utc)
    for _ in range(10):
        row = {"caseId": case_id, "timestamp": _iso_ms(when), "actor": actor, "action": action, "detail": detail}
        if db.put_audit_row(row):
            return row
        when += timedelta(milliseconds=1)
    raise RuntimeError(f"Could not write audit row for {case_id}")


def list_audit(case_id):
    """Return the case's audit rows, oldest first."""
    return db.list_audit_rows(case_id)
