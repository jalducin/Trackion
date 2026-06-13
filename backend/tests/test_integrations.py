"""Pruebas del módulo de integraciones: registry, dispatch (aislamiento) y firma de webhook."""
from app import integrations
from app.integrations.base import Integration
from app.integrations.webhook import WebhookIntegration


def test_registry_has_webhook():
    assert integrations.get("webhook") is not None
    assert "webhook" in [i.name for i in integrations.all()]


def test_register_new_without_touching_core():
    class Dummy(Integration):
        name = "dummy-test"
        description = "demo"
        supported_events = ("ticket.created",)

        def handle(self, event, payload, conf):
            return {"ok": True}

    integrations.register(Dummy())
    assert integrations.get("dummy-test") is not None


def test_dispatch_isolates_failures(monkeypatch):
    calls = {"ok": 0}

    class Boom(Integration):
        name = "boom"
        supported_events = ("ticket.created",)

        def handle(self, event, payload, conf):
            raise RuntimeError("falla intencional")

    class Works(Integration):
        name = "works"
        supported_events = ("ticket.created",)

        def handle(self, event, payload, conf):
            calls["ok"] += 1
            return {"done": True}

    integrations.register(Boom())
    integrations.register(Works())

    # Simula que ambas están activas y suscritas al evento.
    monkeypatch.setattr(integrations, "_active_configs", lambda event=None: [
        {"name": "boom", "config": {}, "events": ["ticket.created"]},
        {"name": "works", "config": {}, "events": ["ticket.created"]},
    ])
    logs = []
    monkeypatch.setattr(integrations, "_log", lambda *a, **k: logs.append(a))

    results = integrations.dispatch("ticket.created", {"id": 1})
    statuses = {r["name"]: r["status"] for r in results}
    assert statuses["boom"] == "error"
    assert statuses["works"] == "ok"
    assert calls["ok"] == 1  # la falla de 'boom' no impidió ejecutar 'works'


def test_webhook_signature_verification():
    wh = WebhookIntegration()
    conf = {"secret": "s3cr3t"}
    body = '{"hello":"world"}'
    import hashlib
    import hmac
    sig = "sha256=" + hmac.new(b"s3cr3t", body.encode(), hashlib.sha256).hexdigest()
    assert wh.verify_inbound({"x-trackion-signature": sig}, body, conf) is True
    assert wh.verify_inbound({"x-trackion-signature": "sha256=bad"}, body, conf) is False
    assert wh.verify_inbound({}, body, {}) is False  # sin secreto → rechaza
