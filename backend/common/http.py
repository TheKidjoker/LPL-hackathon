"""Request and response helpers shared by every handler. Owner: Kaylin."""

import contextvars
import functools
import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Role",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
}

# Sites allowed to call the API from a browser (comma list). "*" allows any site.
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*")

# The calling site's Origin header, set per request by api_handler.
_origin = contextvars.ContextVar("origin", default=None)


def cors_headers(origin=None):
    """CORS headers that echo the caller's Origin only if it is on the allowlist."""
    headers = dict(CORS_HEADERS)
    allowed = [o.strip() for o in ALLOWED_ORIGINS.split(",") if o.strip()]
    if "*" in allowed:
        headers["Access-Control-Allow-Origin"] = "*"
    elif origin and origin in allowed:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Vary"] = "Origin"
    return headers


class ApiError(Exception):
    """Raise from a handler to return an error in the api.md shape."""

    def __init__(self, status, code, message):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


def respond(body, status=200):
    return {"statusCode": status, "headers": cors_headers(_origin.get()), "body": json.dumps(body, default=str)}


def parse_body(event):
    raw = event.get("body") or "{}"
    try:
        body = json.loads(raw)
    except json.JSONDecodeError:
        raise ApiError(400, "bad_request", "Body is not valid JSON.")
    if not isinstance(body, dict):
        raise ApiError(400, "bad_request", "Body must be a JSON object.")
    return body


def require(body, *fields):
    missing = [f for f in fields if body.get(f) in (None, "")]
    if missing:
        raise ApiError(400, "bad_request", f"Missing field(s): {', '.join(missing)}.")


def path_param(event, name):
    value = (event.get("pathParameters") or {}).get(name)
    if not value:
        raise ApiError(400, "bad_request", f"Missing path parameter {name}.")
    return value


def api_handler(fn):
    """Turns ApiError into an error response and hides unexpected errors from callers."""

    @functools.wraps(fn)
    def wrapper(event, context):
        headers = {k.lower(): v for k, v in ((event or {}).get("headers") or {}).items()}
        _origin.set(headers.get("origin"))
        try:
            return fn(event, context)
        except ApiError as e:
            return respond({"error": {"code": e.code, "message": e.message}}, e.status)
        except Exception:
            logger.exception("Unhandled error")
            return respond({"error": {"code": "server_error", "message": "Something went wrong."}}, 500)

    return wrapper
