"""Case statuses and the moves allowed between them. Owner: Krish.

This table is the contract from docs/TEAM_PLAN.md. Change it only by pull request.
"""

HELD = "HELD"
RELEASED = "RELEASED"
EXTENDED = "EXTENDED"
ESCALATED = "ESCALATED"

HOLD_THRESHOLD = 70
HOLD_BUSINESS_DAYS = 10

# (from_status, to_status) -> roles allowed to make the move
MOVES = {
    (None, HELD): {"system"},
    (None, RELEASED): {"system"},
    (HELD, RELEASED): {"fraud"},
    (HELD, EXTENDED): {"fraud"},
    (HELD, ESCALATED): {"fraud"},
    (EXTENDED, RELEASED): {"fraud"},
    (EXTENDED, ESCALATED): {"fraud"},
}

ACTION_TO_STATUS = {"release": RELEASED, "extend": EXTENDED, "escalate": ESCALATED}


def can_move(from_status, to_status, role):
    return role in MOVES.get((from_status, to_status), set())
