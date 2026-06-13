"""Pruebas del router y utilidades HTTP."""
import json

import pytest

import handler
from app.http import ApiError, build_response, parse_body, require_field


def test_routes_registered():
    expected = [
        "GET /trackion/health",
        "POST /trackion/auth/login",
        "GET /trackion/tickets",
        "POST /trackion/tickets/{id}/assign",
        "POST /trackion/integrations/{name}/webhook",
        "GET /trackion/integrations",
    ]
    for key in expected:
        assert key in handler.ROUTES


def test_unknown_route_returns_404():
    resp = handler.api({"routeKey": "GET /trackion/nope"}, None)
    assert resp["statusCode"] == 404


def test_health_route_does_not_require_schema(monkeypatch):
    # health no debe disparar ensure_schema; simulamos DB caída → 503
    monkeypatch.setattr(handler.db, "db_up", lambda: False)
    called = {"schema": False}
    monkeypatch.setattr(handler, "_ensure_once", lambda: called.__setitem__("schema", True))
    resp = handler.api({"routeKey": "GET /trackion/health"}, None)
    assert resp["statusCode"] == 503
    assert called["schema"] is False


def test_parse_body_invalid_json():
    with pytest.raises(ApiError):
        parse_body({"body": "{no-json"})


def test_parse_body_empty():
    assert parse_body({"body": None}) == {}


def test_require_field_missing():
    with pytest.raises(ApiError):
        require_field({}, "email")


def test_build_response_serializes():
    resp = build_response(200, {"a": 1})
    assert resp["statusCode"] == 200
    assert json.loads(resp["body"]) == {"a": 1}
