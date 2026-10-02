"""Request and response helpers shared by every handler. Owner: Krish."""

import functools
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,X-Role",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
}


class ApiError(Exception):
    """Raise from a handler to return an error in the api.md shape."""

    def __init__(self, status, code, message):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


def respond(body, status=200):
    return {"statusCode": status, "headers": CORS_HEADERS, "body": json.dumps(body, default=str)}


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
        try:
            return fn(event, context)
        except ApiError as e:
            return respond({"error": {"code": e.code, "message": e.message}}, e.status)
        except Exception:
            logger.exception("Unhandled error")
            return respond({"error": {"code": "server_error", "message": "Something went wrong."}}, 500)

    return wrapper
