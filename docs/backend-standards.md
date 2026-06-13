# Estándares — Backend (serverless Python)

> Específicos de Trackion. Complementan `docs/base-standards.md`. El backend vive en `backend/`.

## 1. Stack y restricciones

- **Python 3.12**, AWS Lambda, Serverless Framework v3, API Gateway HTTP API (payload 2.0).
- **Solo dependencias puras-Python** (vendorizadas en `backend/vendor/`, agregadas a `sys.path`).
  Está prohibido introducir dependencias con extensiones nativas (no hay build con Docker en este flujo).
  - PostgreSQL: `pg8000` (no `psycopg2`).
  - JWT: `PyJWT`.
  - Hash de password: `hashlib.pbkdf2_hmac` de la stdlib (no `bcrypt`/`passlib`).
- **Sin credenciales en código ni YAML.** Todo secreto se resuelve desde SSM (`/trackion/...`) y llega
  al Lambda como variable de entorno vía `serverless.yml`.

## 2. Arquitectura por capas

```
backend/
├── serverless.yml            # IaC: define el servicio trackion, funciones y recursos
├── requirements.txt          # deps puras-python a vendorizar
├── handler.py                # entrypoint Lambda: router HTTP → handlers de cada capability
├── app/
│   ├── __init__.py
│   ├── config.py             # lee env (DB_*, JWT_SECRET, etc.)
│   ├── db.py                 # capa de datos: conexión pg8000 + helpers query/execute + ensure_schema
│   ├── http.py               # helpers de request/response (parse body, build_response, errores)
│   ├── auth.py               # login (PBKDF2), emisión/validación JWT, dependencia de identidad
│   ├── tickets.py            # servicio + handlers de tickets (CRUD, asignación, comentarios, estados)
│   ├── catalog.py            # servicio + handlers de categorías/subcategorías/prioridades/usuarios
│   └── integrations/         # módulo de integraciones EXTENSIBLE (ver §4)
│       ├── __init__.py       # registry + dispatch de eventos
│       ├── base.py           # contrato Integration (protocolo) + clase base
│       └── webhook.py        # integración de ejemplo: webhook genérico de salida
└── tests/                    # pruebas con pytest (capa de datos en sqlite/mocks o pg de prueba)
```

- **entrypoints** parsean el evento y delegan; no contienen lógica de negocio.
- **servicio** contiene la lógica; recibe/retorna dicts o dataclasses; no conoce el evento HTTP.
- **datos** (`db.py`) expone `query()`, `execute()`, `tx()` con SQL **parametrizado** (nunca f-strings con datos).

## 3. Base de datos (PostgreSQL)

- Esquema idempotente en `ensure_schema()` con `CREATE TABLE IF NOT EXISTS` + `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`.
- Toda tabla con `id` serial/identity, `created_at`/`updated_at` (timestamptz), y FKs explícitas.
- Migraciones de columnas siempre aditivas e idempotentes (no romper datos existentes).
- Pensar las tablas para que **Grafana** pueda graficar: timestamps, estados y prioridades normalizados.

## 4. Módulo de integraciones (abierto/extensible)

Requisito de producto: **no acoplarse a ningún proveedor**. El núcleo emite eventos de dominio
(`ticket.created`, `ticket.assigned`, `ticket.status_changed`, `ticket.commented`) y el módulo de
integraciones los entrega a las integraciones registradas.

- `base.py` define el contrato `Integration` (atributo `name`, método `handle(event, payload)` y
  `verify(config)`), y una clase base con utilidades.
- `__init__.py` mantiene un **registry** (`register()` / `get()` / `all()`) y un `dispatch(event, payload)`
  que recorre las integraciones activas. Las integraciones se activan/configuran por datos
  (tabla `integrations`), no por código.
- Entrada (inbound): endpoint genérico `POST /trackion/integrations/{name}/webhook` que enruta al
  handler inbound de la integración correspondiente. Validación de firma/secreto por integración.
- Agregar una integración nueva = crear un archivo en `integrations/` y registrarlo; **cero cambios** en el núcleo.

## 5. HTTP y errores

- Respuestas JSON con `build_response(status, body)`; CORS gestionado por API Gateway.
- Errores de dominio → 4xx con `{ "error": { "code", "message" } }`; errores no controlados → 500 con log.
- Rutas protegidas exigen JWT válido (authorizer); rutas públicas: `/trackion/health` y los webhooks inbound.

## 6. Pruebas y verificación (obligatorio, ver regla de tasks)

- Unitarias de servicio y de la capa de datos.
- Verificación manual del agente: `serverless package` debe pasar; tras deploy, probar endpoints con `curl`
  (login → crear ticket → listar → asignar → comentar) y restaurar estado de datos de prueba.
