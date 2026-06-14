"""Servidor HTTP local que envuelve los handlers Lambda (para correr Trackion con Docker, sin AWS).

Traduce cada petición HTTP al formato de evento de API Gateway HTTP API (payload 2.0) y delega en
`handler.api` / `handler.authorizer`. Así el MISMO código de negocio corre local e idéntico a producción.
No usar en producción: es solo para desarrollo/local.
"""
import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

import handler  # importa app/* (config desde env)

# Rutas públicas (sin authorizer), igual que serverless.yml.
PUBLIC = {
    "GET /trackion/health",
    "POST /trackion/auth/login",
    "POST /trackion/integrations/{name}/webhook",
}

# Precompila los templates de ROUTES a regex para extraer pathParameters localmente.
_COMPILED = []
for route_key in handler.ROUTES:
    method, template = route_key.split(" ", 1)
    pattern = "^" + re.sub(r"\{([^}]+)\}", r"(?P<\1>[^/]+)", template) + "$"
    _COMPILED.append((method, template, route_key, re.compile(pattern)))


def _match(method, path):
    for m, _template, route_key, rx in _COMPILED:
        if m != method:
            continue
        mo = rx.match(path)
        if mo:
            return route_key, mo.groupdict()
    return None, {}


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")

    def _send(self, status, body, headers=None):
        self.send_response(status)
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self._cors()
        self.end_headers()
        if body is not None:
            self.wfile.write(body.encode("utf-8") if isinstance(body, str) else body)

    def _dispatch(self, method):
        parsed = urlparse(self.path)
        path = parsed.path
        route_key, path_params = _match(method, path)
        if route_key is None:
            self._send(404, json.dumps({"error": {"code": "no_route", "message": f"Ruta no encontrada: {method} {path}"}}))
            return

        length = int(self.headers.get("Content-Length", 0) or 0)
        raw_body = self.rfile.read(length).decode("utf-8") if length else ""
        headers = {k.lower(): v for k, v in self.headers.items()}
        qs = {k: v[0] for k, v in parse_qs(parsed.query).items()}

        event = {
            "routeKey": route_key,
            "rawPath": path,
            "headers": headers,
            "body": raw_body or None,
            "pathParameters": path_params or None,
            "queryStringParameters": qs or None,
            "requestContext": {"http": {"method": method, "path": path}},
        }

        # Authorizer local para rutas protegidas (replica el flujo de API Gateway).
        if route_key not in PUBLIC:
            auth_result = handler.authorizer(event, None)
            if not auth_result.get("isAuthorized"):
                self._send(401, json.dumps({"error": {"code": "unauthorized", "message": "No autorizado"}}))
                return
            event["requestContext"]["authorizer"] = {"lambda": auth_result.get("context", {})}

        resp = handler.api(event, None)
        self._send(resp.get("statusCode", 200), resp.get("body", ""), resp.get("headers"))

    def do_OPTIONS(self):
        self._send(204, None)

    def do_GET(self):
        self._dispatch("GET")

    def do_POST(self):
        self._dispatch("POST")

    def do_PUT(self):
        self._dispatch("PUT")

    def do_DELETE(self):
        self._dispatch("DELETE")

    def log_message(self, fmt, *args):
        print("[trackion]", fmt % args)


def main():
    import os
    port = int(os.environ.get("PORT", "8080"))
    print(f"Trackion local en http://0.0.0.0:{port}/trackion")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
