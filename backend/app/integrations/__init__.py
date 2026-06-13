"""Registry de integraciones + dispatch de eventos de dominio (con aislamiento de fallos).

Agregar una integración nueva = crear su archivo, instanciar y `register(...)` aquí. CERO cambios
en el núcleo (tickets/catalog/auth). La activación y configuración viven en la tabla `integrations`.
"""
import json

from .base import Integration
from .webhook import WebhookIntegration

_REGISTRY: dict = {}


def register(integration: Integration):
    _REGISTRY[integration.name] = integration
    return integration


def get(name: str):
    return _REGISTRY.get(name)


def all():
    return list(_REGISTRY.values())


# ── Registro de integraciones disponibles ──
register(WebhookIntegration())


def _active_configs(event: str = None):
    """Lee de la tabla `integrations` las integraciones activas (opcionalmente suscritas a un evento)."""
    from .. import db
    rows = db.query("SELECT name, is_active, config, events FROM integrations WHERE is_active = TRUE")
    result = []
    for row in rows:
        events = row.get("events") or []
        if event is not None and event not in events:
            continue
        conf = row.get("config")
        if isinstance(conf, str):
            try:
                conf = json.loads(conf)
            except ValueError:
                conf = {}
        result.append({"name": row["name"], "config": conf or {}, "events": events})
    return result


def _log(name: str, event: str, status: str, detail: str = ""):
    from .. import db
    try:
        db.execute(
            """INSERT INTO integrations_log (integration_name, event, status, detail)
               VALUES (:n, :e, :s, :d)""",
            n=name, e=event, s=status, d=(detail or "")[:2000],
        )
    except Exception:
        pass  # el logging de integraciones nunca debe romper la operación


def dispatch(event: str, payload: dict):
    """Entrega `event` a las integraciones activas suscritas. Aísla fallos por integración."""
    results = []
    for active in _active_configs(event):
        integ = get(active["name"])
        if integ is None:
            _log(active["name"], event, "skipped", "integración no registrada en código")
            continue
        try:
            out = integ.handle(event, payload, active["config"])
            _log(integ.name, event, "ok", json.dumps(out, default=str) if out else "")
            results.append({"name": integ.name, "status": "ok"})
        except Exception as exc:  # aislamiento: un fallo no detiene a las demás
            _log(integ.name, event, "error", str(exc))
            results.append({"name": integ.name, "status": "error", "detail": str(exc)})
    return results
