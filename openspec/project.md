# Contexto del proyecto — Trackion

## Qué es

**Trackion** es un sistema de mesa de ayuda (helpdesk) propio: permite levantar, categorizar,
priorizar, asignar y dar seguimiento a tickets de soporte. Está pensado como producto autónomo y
white-label (sin acoplarse a ningún proveedor externo de tickets).

Incluye un **módulo de integración de APIs abierto y extensible**: cualquier sistema externo puede
conectarse mediante integraciones registrables (salida vía dispatch de eventos, entrada vía webhooks),
sin que el núcleo dependa de un proveedor concreto.

## Stack tecnológico

- Lenguaje: Python 3.12 (identificadores en inglés; documentación y comentarios en español).
- Compute / IaC: AWS Lambda + Serverless Framework v3.
- HTTP: API Gateway V2 (HTTP API), base path `/trackion`.
- Base de datos: **PostgreSQL** (driver puro-Python `pg8000`, SQL parametrizado).
- Auth: JWT (PyJWT) con authorizer de API Gateway; passwords con PBKDF2 (stdlib `hashlib`).
- Monitoreo: PostgreSQL como fuente de datos para **Grafana**; endpoint `/trackion/health`.
- Frontend: HTML + CSS + JavaScript vanilla (SPA ligera), paleta visual metálica.

## Arquitectura

Arquitectura por capas dentro de un backend serverless:

```
Frontend (SPA vanilla)  ──HTTPS──>  API Gateway HTTP API (/trackion/*)
                                          │  authorizer JWT
                                          ▼
                         Lambda  trackion-api  (router → handlers)
        ┌───────────────┬───────────────┬───────────────┬──────────────────┐
        │  auth         │  tickets      │  catalog      │  integrations     │
        │  (login/me)   │  (CRUD+asig)  │  (cat/pri/usr)│  (registry+hooks) │
        └───────────────┴───────────────┴───────────────┴──────────────────┘
                                          │  capa de datos (pg8000)
                                          ▼
                                   PostgreSQL  (schema trackion)
```

- **Capa de presentación (entrypoints)**: handlers Lambda que parsean el evento HTTP y delegan.
- **Capa de servicio**: lógica de negocio (tickets, catálogo, integraciones).
- **Capa de datos**: acceso a PostgreSQL con SQL parametrizado; esquema idempotente (`ensure_schema`).
- **Integraciones**: registro de integraciones (patrón plugin) desacoplado del núcleo.

## Convenciones

- Idioma: documentación y comentarios en **español**; identificadores de código en inglés.
- Commits: conventional commits.
- Ramas: `feature/[change-name]`.
- Estándares por área: `docs/backend-standards.md`, `docs/frontend-standards.md`.
- Sin credenciales en código ni YAML: todo secreto vive en **SSM Parameter Store** (`/trackion/...`).

## Comandos clave

- Instalar deps backend (puras Python, vendorizadas): `python -m pip install -r backend/requirements.txt -t backend/vendor`
- Validar empaquetado: `cd backend && serverless package --stage develop`
- Desplegar: `cd backend && serverless deploy --stage develop`
- Desplegar una función: `serverless deploy function --function api --stage develop`
- Pruebas: `python -m pytest backend/tests`
- Frontend (local): servir `frontend/` con cualquier server estático (`python -m http.server`).
