"""Contrato base de una integración. Toda integración nueva hereda de `Integration`."""
from typing import Iterable


class Integration:
    """Contrato de integración (patrón plugin), desacoplado del núcleo.

    Una integración declara su `name`, los eventos de dominio que soporta y cómo manejarlos
    (salida) y/o cómo procesar webhooks entrantes (entrada). El núcleo no la conoce: se descubre
    vía el registry y se activa por datos (tabla `integrations`).
    """

    #: Identificador único de la integración (kebab/lower).
    name: str = ""
    #: Descripción legible.
    description: str = ""
    #: Eventos de dominio que la integración puede manejar de salida.
    supported_events: Iterable[str] = ()

    def handle(self, event: str, payload: dict, conf: dict) -> dict:
        """Maneja un evento de dominio de SALIDA. `conf` es la config activa (tabla integrations).

        Debe ser idempotente y no lanzar para errores esperados; retorna un dict con el resultado.
        """
        raise NotImplementedError

    def verify_inbound(self, headers: dict, raw_body: str, conf: dict) -> bool:
        """Valida un webhook de ENTRADA (firma/secreto). Por defecto, rechaza."""
        return False

    def handle_inbound(self, headers: dict, body: dict, conf: dict) -> dict:
        """Procesa un webhook de ENTRADA ya validado."""
        raise NotImplementedError
