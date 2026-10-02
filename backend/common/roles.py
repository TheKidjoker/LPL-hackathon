"""Reads the caller's role. Owner: Kaylin.

In AWS, API Gateway's Cognito authorizer verifies the caller's ID token, and the role is the
caller's Cognito group (client, advisor, or fraud), read from the token claims. Nobody can
choose their role by setting a header.

The X-Role header is only honored when ALLOW_ROLE_HEADER=true: local runs and tests, never
the deployed stack.
"""

import os

from common.http import ApiError

ROLES = ("client", "advisor", "fraud")


def _groups(claims):
    """cognito:groups arrives as "fraud", "[fraud advisor]", or "fraud,advisor"."""
    raw = (claims or {}).get("cognito:groups") or ""
    if isinstance(raw, (list, tuple)):
        return [str(g).strip().lower() for g in raw]
    return [g.strip().lower() for g in str(raw).strip("[]").replace(",", " ").split() if g.strip()]


def get_role(event):
    claims = ((event.get("requestContext") or {}).get("authorizer") or {}).get("claims")
    role = next((g for g in _groups(claims) if g in ROLES), None)
    if role is None and os.environ.get("ALLOW_ROLE_HEADER", "").lower() == "true":
        headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
        role = (headers.get("x-role") or "").strip().lower()
    if role not in ROLES:
        raise ApiError(403, "forbidden", "Sign in as a client, advisor, or fraud team member.")
    return role


def require_role(event, *allowed):
    role = get_role(event)
    if role not in allowed:
        raise ApiError(403, "forbidden", f"This action is for: {', '.join(allowed)}.")
    return role
