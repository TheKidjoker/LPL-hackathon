"""Audit log. Owner: Krish. Every change to a Case writes one row."""


def write_audit(case_id, actor, action, detail=""):
    """Write {caseId, timestamp, actor, action, detail} to the Audit table."""
    raise NotImplementedError


def list_audit(case_id):
    """Return the case's audit rows, oldest first."""
    raise NotImplementedError
