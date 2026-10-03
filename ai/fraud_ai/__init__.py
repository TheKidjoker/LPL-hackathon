"""Everything Claude does. Owner: Thomas.

Handlers import only these functions. Their signatures and return shapes
are the contract in docs/api.md and docs/TEAM_PLAN.md.
"""

from fraud_ai.contact_check import check_contact
from fraud_ai.scam_chat import scam_check_chat
from fraud_ai.score import score_withdrawal

__all__ = ["score_withdrawal", "scam_check_chat", "check_contact"]
