"""POST /cases/{caseId}/decision. Owner: Kaylin.

The fraud team releases, extends, or escalates a hold. Only the fraud role can decide, and only
the moves in case_state.MOVES are allowed (409 otherwise). Release clears the hold end date,
extend moves it to 15 business days after the request (Rule 2165's limit), and escalate keeps it. Every decision is audited.
"""

from datetime import date, datetime, timezone

from common import audit, case_state, db
from common.http import ApiError, api_handler, parse_body, path_param, require, respond
from common.roles import require_role
from common.views import case_for_role

MAX_NOTE = 2000


def new_hold_end(case, to_status, today):
    if to_status == case_state.RELEASED:
        return None
    if to_status == case_state.EXTENDED:
        created = (case.get("createdAt") or "")[:10]
        start = date.fromisoformat(created) if created else today
        extended = case_state.hold_end_date(start, case_state.EXTENDED_HOLD_BUSINESS_DAYS)
        return max(extended, case.get("holdEndsAt") or extended)
    return case.get("holdEndsAt")


@api_handler
def handler(event, context):
    role = require_role(event, "fraud")
    case_id = path_param(event, "caseId")
    body = parse_body(event)
    require(body, "action")
    to_status = case_state.ACTION_TO_STATUS.get(body["action"])
    if not to_status:
        raise ApiError(400, "bad_request", "action must be release, extend, or escalate.")
    note = body.get("note") or ""
    if not isinstance(note, str) or len(note) > MAX_NOTE:
        raise ApiError(400, "bad_request", f"note must be a string of at most {MAX_NOTE} characters.")

    case = db.get_case(case_id)
    if case is None:
        raise ApiError(404, "not_found", f"No case {case_id}.")
    from_status = case["status"]
    if not case_state.can_move(from_status, to_status, role):
        raise ApiError(409, "invalid_move", f"Cannot move a {from_status} case to {to_status}.")

    now = datetime.now(timezone.utc)
    changes = {
        "status": to_status,
        "holdEndsAt": new_hold_end(case, to_status, now.date()),
        "decision": {"action": body["action"], "by": role, "at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "note": note.strip()},
    }
    updated = db.update_case(case_id, changes, if_status=from_status)
    if updated is None:  # another reviewer decided between our read and our write
        raise ApiError(409, "invalid_move", "This case was just updated by someone else. Reload it and try again.")

    detail = note.strip() or f"{from_status} to {to_status}"
    if to_status == case_state.EXTENDED:
        detail += f" (hold now ends {changes['holdEndsAt']})"
    audit.write_audit(case_id, role, to_status, detail[:200])
    updated["audit"] = audit.list_audit(case_id)
    return respond(case_for_role(updated, role))
