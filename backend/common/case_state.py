"""Case statuses and the moves allowed between them. Owner: Kaylin.

This table is the contract from docs/TEAM_PLAN.md. Change it only by pull request.
"""

from datetime import timedelta

HELD = "HELD"
RELEASED = "RELEASED"
EXTENDED = "EXTENDED"
ESCALATED = "ESCALATED"

HOLD_THRESHOLD = 70
# A new hold gives the fraud team 2 business days to review. Extending it moves the end to
# 15 business days after the request: FINRA Rule 2165's initial limit for clients 65 and older.
HOLD_BUSINESS_DAYS = 2
EXTENDED_HOLD_BUSINESS_DAYS = 15

# (from_status, to_status) -> roles allowed to make the move
MOVES = {
    (None, HELD): {"system"},
    (None, RELEASED): {"system"},
    (HELD, RELEASED): {"fraud"},
    (HELD, EXTENDED): {"fraud"},
    (HELD, ESCALATED): {"fraud"},
    (EXTENDED, RELEASED): {"fraud"},
    (EXTENDED, ESCALATED): {"fraud"},
    # After investigations clears an escalated case, the fraud team can still release it
    # (with a logged reason). Nothing else leaves ESCALATED.
    (ESCALATED, RELEASED): {"fraud"},
}

ACTION_TO_STATUS = {"release": RELEASED, "extend": EXTENDED, "escalate": ESCALATED}


def can_move(from_status, to_status, role):
    return role in MOVES.get((from_status, to_status), set())


def hold_end_date(start, business_days=HOLD_BUSINESS_DAYS):
    """The date `business_days` weekdays after `start` (a date), as YYYY-MM-DD."""
    day = start
    while business_days:
        day += timedelta(days=1)
        if day.weekday() < 5:
            business_days -= 1
    return day.isoformat()
