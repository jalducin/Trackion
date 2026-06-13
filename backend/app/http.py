"""Utilidades HTTP para handlers Lambda sobre API Gateway HTTP API (payload 2.0)."""
import json


class ApiError(Exception):
    """Error de dominio que se traduce a una respuesta HTTP controlada."""

    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


def build_response(status: int, body, headers=None):
    """Construye la respuesta esperada por API Gateway (payload 2.0)."""
    base = {"Content-Type": "application/json"}
    if headers:
        base.update(headers)
    return {
        "statusCode": status,
        "headers": base,
        "body": body if isinstance(body, str) else json.dumps(body, default=str),
    }


def error_response(err: "ApiError"):
    return build_response(err.status, {"error": {"code": err.code, "message": err.message}})


def parse_body(event) -> dict:
    """Devuelve el body JSON como dict (o {} si está vacío); lanza ApiError si es inválido."""
    raw = event.get("body")
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        raise ApiError(400, "invalid_body", "El cuerpo de la petición no es JSON válido")
    if not isinstance(data, dict):
        raise ApiError(400, "invalid_body", "El cuerpo debe ser un objeto JSON")
    return data


def path_param(event, name: str):
    return (event.get("pathParameters") or {}).get(name)


def query_params(event) -> dict:
    return event.get("queryStringParameters") or {}


def identity(event) -> dict:
    """Identidad del usuario inyectada por el authorizer (rutas protegidas)."""
    ctx = (event.get("requestContext") or {}).get("authorizer") or {}
    return ctx.get("lambda") or ctx or {}


def require_field(data: dict, name: str):
    value = data.get(name)
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ApiError(400, "missing_field", f"Falta el campo requerido: {name}")
    return value
