## Why

Trackion necesita un núcleo de mesa de ayuda funcional y desplegable que permita operar tickets de
soporte de punta a punta, sin acoplarse a ningún proveedor externo, y con monitoreo vía Grafana sobre
PostgreSQL. Este es el MVP que habilita todo lo demás.

## What Changes

- Backend serverless en Python 3.12 (AWS Lambda + Serverless Framework v3 + API Gateway HTTP API),
  servicio nuevo y aislado `trackion`, base path `/trackion`.
- Autenticación por **JWT** (login con email/password, PBKDF2) y authorizer de API Gateway.
- **Tickets**: crear, listar (con filtros), ver detalle, actualizar, cambiar estado, **asignar** y comentar.
- **Catálogos**: categorías, subcategorías, prioridades y usuarios/agentes (CRUD administrable).
- **Módulo de integraciones extensible** (no acoplado): registry de integraciones de salida
  (dispatch de eventos de dominio) + webhooks de entrada genéricos. Una integración de ejemplo (webhook).
- **Observabilidad**: endpoint `/trackion/health` y esquema PostgreSQL pensado para Grafana.
- Persistencia en **PostgreSQL** con esquema idempotente (`ensure_schema`) y datos semilla.

## Capabilities

### New Capabilities
- `auth`: autenticación JWT, login y validación de identidad para rutas protegidas.
- `tickets`: ciclo de vida del ticket (CRUD, estados, asignación, comentarios).
- `catalog`: administración de categorías, subcategorías, prioridades y usuarios.
- `integrations`: módulo extensible de integración de APIs (salida por eventos, entrada por webhooks).
- `observability`: salud del servicio y modelo de datos apto para monitoreo con Grafana.

### Modified Capabilities
- (ninguna — proyecto nuevo)

## Impact

- Nuevo código en `backend/` (Lambda Python, capa de datos pg8000, módulo de integraciones).
- Nuevo frontend en `frontend/` (SPA vanilla, paleta metálica).
- Infra AWS nueva: servicio `trackion-develop` (API GW, Lambdas, authorizer), SSM `/trackion/...`.
- Dependencias puras-Python: `pg8000`, `PyJWT` (vendorizadas).
- CI/CD: GitHub Actions → AWS (deploy desde el segundo push).
