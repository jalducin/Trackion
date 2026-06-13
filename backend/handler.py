"""Entrypoint Lambda de Trackion: authorizer JWT + router HTTP (API Gateway HTTP API v2.0).

Las dependencias puras-Python viven en `vendor/` (ver docs/backend-standards.md §1) y se agregan
a `sys.path` antes de importarlas.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "vendor"))

from app import auth, catalog, config, db, integrations, tickets  # noqa: E402
from app.http import ApiError, build_response, error_response, path_param  # noqa: E402

_SCHEMA_READY = False


def _ensure_once():
    global _SCHEMA_READY
    if not _SCHEMA_READY:
        db.ensure_schema()
        _SCHEMA_READY = True


# ───────────────────────── Authorizer (JWT) ─────────────────────────

def authorizer(event, context):
    """Request authorizer (simple response) para API Gateway HTTP API."""
    token = auth.bearer_from_header(_header(event, "authorization"))
    if not token:
        return {"isAuthorized": False}
    try:
        claims = auth.decode_token(token)
    except ApiError:
        return {"isAuthorized": False}
    return {
        "isAuthorized": True,
        "context": {
            "sub": claims.get("sub"),
            "email": claims.get("email"),
            "name": claims.get("name"),
            "role": claims.get("role"),
        },
    }


def _header(event, name: str):
    headers = event.get("headers") or {}
    return headers.get(name) or headers.get(name.title()) or headers.get(name.upper())


# ───────────────────────── Health ─────────────────────────

def _health(event):
    up = db.db_up()
    if not up:
        return build_response(503, {"status": "degraded", "db": "down", "version": config.APP_VERSION})
    return build_response(200, {"status": "ok", "db": "up", "version": config.APP_VERSION})


# ───────────────────────── Integraciones (handlers) ─────────────────────────

def _list_integrations(event):
    db_rows = {r["name"]: r for r in db.query("SELECT name, is_active, events FROM integrations")}
    items = []
    for integ in integrations.all():
        row = db_rows.get(integ.name, {})
        items.append({
            "name": integ.name,
            "description": integ.description,
            "supported_events": list(integ.supported_events),
            "is_active": bool(row.get("is_active", False)),
            "events": row.get("events") or [],
        })
    return build_response(200, {"items": items})


def _inbound_webhook(event):
    name = path_param(event, "name")
    integ = integrations.get(name)
    if integ is None:
        raise ApiError(404, "not_found", f"Integración no registrada: {name}")
    row = db.query_one("SELECT config FROM integrations WHERE name = :n", n=name)
    conf = row["config"] if row else {}
    if isinstance(conf, str):
        try:
            conf = json.loads(conf)
        except ValueError:
            conf = {}
    raw_body = event.get("body") or ""
    if not integ.verify_inbound(event.get("headers") or {}, raw_body, conf or {}):
        raise ApiError(401, "invalid_signature", "Firma o secreto inválido")
    try:
        body = json.loads(raw_body) if raw_body else {}
    except ValueError:
        body = {}
    result = integ.handle_inbound(event.get("headers") or {}, body, conf or {})
    return build_response(200, {"ok": True, "result": result})


# ───────────────────────── Router ─────────────────────────

ROUTES = {
    "GET /trackion/health": _health,
    "POST /trackion/auth/login": auth.login,
    "GET /trackion/auth/me": auth.me,
    "POST /trackion/integrations/{name}/webhook": _inbound_webhook,
    "GET /trackion/integrations": _list_integrations,

    "GET /trackion/tickets": tickets.list_tickets,
    "POST /trackion/tickets": tickets.create_ticket,
    "GET /trackion/tickets/{id}": tickets.get_ticket,
    "PUT /trackion/tickets/{id}": tickets.update_ticket,
    "POST /trackion/tickets/{id}/assign": tickets.assign_ticket,
    "GET /trackion/tickets/{id}/comments": tickets.list_comments,
    "POST /trackion/tickets/{id}/comments": tickets.add_comment,

    "GET /trackion/catalog/categories": catalog.list_categories,
    "POST /trackion/catalog/categories": catalog.create_category,
    "PUT /trackion/catalog/categories/{id}": catalog.update_category,
    "GET /trackion/catalog/subcategories": catalog.list_subcategories,
    "POST /trackion/catalog/subcategories": catalog.create_subcategory,
    "PUT /trackion/catalog/subcategories/{id}": catalog.update_subcategory,
    "GET /trackion/catalog/priorities": catalog.list_priorities,
    "POST /trackion/catalog/priorities": catalog.create_priority,
    "PUT /trackion/catalog/priorities/{id}": catalog.update_priority,
    "GET /trackion/catalog/users": catalog.list_users,
    "POST /trackion/catalog/users": catalog.create_user,
    "PUT /trackion/catalog/users/{id}": catalog.update_user,
}

# Rutas que no requieren esquema/BD garantizada antes de ejecutarse.
_NO_SCHEMA = {"GET /trackion/health"}


def api(event, context):
    route_key = event.get("routeKey", "")
    handler = ROUTES.get(route_key)
    if handler is None:
        return build_response(404, {"error": {"code": "no_route", "message": f"Ruta no encontrada: {route_key}"}})
    try:
        if route_key not in _NO_SCHEMA:
            _ensure_once()
        return handler(event)
    except ApiError as err:
        return error_response(err)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR ruta={route_key}: {exc!r}")
        return build_response(500, {"error": {"code": "internal", "message": "Error interno"}})
