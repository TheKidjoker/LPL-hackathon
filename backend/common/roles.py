"""Reads the caller's role. Owner: Kaylin.

For now the frontend sends an X-Role header. Stretch: swap this for the
Cognito group on the authorizer claims, without changing any handler.
"""

from common.http import ApiError

ROLES = ("client", "advisor", "fraud")


def get_role(event):
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    role = (headers.get("x-role") or "").strip().lower()
    if role not in ROLES:
        raise ApiError(403, "forbidden", "Send X-Role: client, advisor, or fraud.")
    return role


def require_role(event, *allowed):
    role = get_role(event)
    if role not in allowed:
        raise ApiError(403, "forbidden", f"This action is for: {', '.join(allowed)}.")
    return role
