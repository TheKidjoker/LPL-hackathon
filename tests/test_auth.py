"""Roles from Cognito claims, the X-Role fallback switch, fraud-only reset, and the CORS allowlist."""

import pytest

from common import http, roles
from common.http import ApiError
from conftest import body
from handlers import demo_reset


def claims_event(groups, headers=None):
    return {"headers": headers or {}, "requestContext": {"authorizer": {"claims": {"cognito:groups": groups}}}}


@pytest.mark.parametrize("groups, role", [
    ("fraud", "fraud"),
    ("[advisor]", "advisor"),
    ("[client fraud]", "client"),
    ("admins,fraud", "fraud"),
    (["advisor"], "advisor"),
])
def test_role_comes_from_cognito_groups(groups, role):
    assert roles.get_role(claims_event(groups)) == role


def test_claims_win_over_a_spoofed_header():
    assert roles.get_role(claims_event("client", {"X-Role": "fraud"})) == "client"


def test_header_ignored_when_fallback_is_off(monkeypatch):
    monkeypatch.setenv("ALLOW_ROLE_HEADER", "false")
    with pytest.raises(ApiError) as e:
        roles.get_role({"headers": {"X-Role": "fraud"}})
    assert e.value.status == 403


def test_header_used_when_fallback_is_on(monkeypatch):
    monkeypatch.setenv("ALLOW_ROLE_HEADER", "true")
    assert roles.get_role({"headers": {"X-Role": "advisor"}}) == "advisor"


def test_unknown_group_is_refused(monkeypatch):
    monkeypatch.setenv("ALLOW_ROLE_HEADER", "false")
    with pytest.raises(ApiError):
        roles.get_role(claims_event("admins"))


@pytest.mark.parametrize("role", ["client", "advisor"])
def test_demo_reset_is_fraud_only(event, seeded, role):
    assert demo_reset.handler(event("demo_reset", headers={"X-Role": role}), None)["statusCode"] == 403


def test_demo_reset_works_for_fraud(event, seeded):
    assert body(demo_reset.handler(event("demo_reset"), None))["ok"] is True


def test_cors_echoes_only_allowed_origins(monkeypatch):
    monkeypatch.setattr(http, "ALLOWED_ORIGINS", "https://app.example,http://localhost:5173")
    assert http.cors_headers("http://localhost:5173")["Access-Control-Allow-Origin"] == "http://localhost:5173"
    assert "Access-Control-Allow-Origin" not in http.cors_headers("https://evil.example")
    assert "Access-Control-Allow-Origin" not in http.cors_headers(None)


def test_cors_wildcard_still_supported(monkeypatch):
    monkeypatch.setattr(http, "ALLOWED_ORIGINS", "*")
    assert http.cors_headers("https://anything.example")["Access-Control-Allow-Origin"] == "*"


def test_handlers_echo_the_request_origin(event, seeded, monkeypatch):
    monkeypatch.setattr(http, "ALLOWED_ORIGINS", "http://localhost:5173")
    result = demo_reset.handler(event("demo_reset", headers={"X-Role": "fraud", "Origin": "http://localhost:5173"}), None)
    assert result["headers"]["Access-Control-Allow-Origin"] == "http://localhost:5173"
