"""Integración de ejemplo: webhook genérico (salida y entrada).

Salida: hace POST del evento+payload a una URL configurada (`config.url`), con un header de firma
HMAC opcional (`config.secret`). Entrada: valida un secreto compartido y acepta el payload.
Sirve de plantilla para integraciones reales (Slack, Asana, Freshdesk, etc.) sin tocar el núcleo.
"""
import hashlib
import hmac
import json
import urllib.request

from .base import Integration


class WebhookIntegration(Integration):
    name = "webhook"
    description = "Webhook genérico: notifica eventos por HTTP POST y acepta webhooks entrantes."
    supported_events = (
        "ticket.created",
        "ticket.assigned",
        "ticket.status_changed",
        "ticket.commented",
    )

    def handle(self, event: str, payload: dict, conf: dict) -> dict:
        url = conf.get("url")
        if not url:
            raise ValueError("config.url no definido para la integración webhook")
        body = json.dumps({"event": event, "data": payload}, default=str).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        secret = conf.get("secret")
        if secret:
            sig = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
            headers["X-Trackion-Signature"] = f"sha256={sig}"
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=8) as resp:
            return {"http_status": resp.status}

    def verify_inbound(self, headers: dict, raw_body: str, conf: dict) -> bool:
        secret = conf.get("secret")
        if not secret:
            return False
        provided = headers.get("x-trackion-signature") or headers.get("X-Trackion-Signature") or ""
        expected = "sha256=" + hmac.new(
            secret.encode("utf-8"), (raw_body or "").encode("utf-8"), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(provided, expected)

    def handle_inbound(self, headers: dict, body: dict, conf: dict) -> dict:
        # Plantilla: registrar/encolar el payload entrante. Aquí solo se hace eco controlado.
        return {"received": True, "keys": sorted(list(body.keys()))}
