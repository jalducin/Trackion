# Arquitectura — Trackion

> Documento canónico de arquitectura. El README enlaza aquí; no duplica este contenido.

## 1. Visión general

Trackion es una mesa de ayuda **serverless** desplegada en AWS. El frontend es una SPA estática servida
por CloudFront; el backend es una función Lambda detrás de API Gateway que habla con PostgreSQL (RDS) y
emite eventos a un módulo de integraciones extensible.

```
┌───────────────────────────────────────────────────────────────────────────┐
│  Navegador — SPA vanilla (paleta metálica)                                  │
└───────────────────────────────────────────────────────────────────────────┘
        │ HTTPS                                   ▲ HTTPS (estático)
        ▼                                         │
┌──────────────────────────┐            ┌─────────────────────────────────────┐
│  API Gateway HTTP API     │            │  CloudFront (OAC) ── S3 privado       │
│  /trackion/*              │            │  index.html · css · js               │
│  authorizer JWT (Lambda)  │            └─────────────────────────────────────┘
└──────────────────────────┘
        │ invoke
        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  Lambda  trackion-api  (handler.py → router por routeKey)                   │
│                                                                             │
│   app/auth.py     app/tickets.py     app/catalog.py     app/integrations/   │
│   (login/JWT)     (CRUD/estado/      (categorías/        (registry +         │
│                    asignación/        subcat/prioridad/   dispatch +         │
│                    comentarios)       usuarios)           webhooks)          │
│                              │                                  │            │
│                              ▼  app/db.py (pg8000, SQL parametrizado)        │
└───────────────────────────────────────────────────────────────────────────┘
        │ TLS 5432                                  │ eventos de dominio
        ▼                                           ▼
┌──────────────────────────┐            ┌─────────────────────────────────────┐
│  RDS PostgreSQL           │──────────▶ │  Integraciones de salida (HTTP)      │
│  (esquema trackion)       │  Grafana   │  + webhooks de entrada               │
└──────────────────────────┘            └─────────────────────────────────────┘
```

## 2. Capas del backend

| Capa | Archivos | Responsabilidad |
|------|----------|-----------------|
| Entrypoint/router | `handler.py` | Parseo del evento HTTP (payload 2.0), authorizer JWT, dispatch por `routeKey`, traducción de `ApiError`→HTTP |
| Servicio | `app/tickets.py`, `app/catalog.py`, `app/auth.py` | Lógica de negocio; no conoce el evento HTTP |
| Datos | `app/db.py` | Conexión pg8000 reutilizable, helpers parametrizados, `ensure_schema()` idempotente + semilla |
| Integraciones | `app/integrations/` | Registry (plugin), `dispatch()` con aislamiento de fallos, webhooks de entrada |
| Soporte | `app/http.py`, `app/config.py` | Respuestas/errores HTTP, configuración desde env |

## 3. Modelo de datos

`users`, `categories`, `subcategories`, `priorities`, `tickets`, `ticket_comments`,
`integrations`, `integrations_log`. Detalle de columnas en
`openspec/changes/helpdesk-mvp/design.md` (sección *Data model*). Timestamps y estados normalizados para
que **Grafana** grafique volumen, backlog y tiempos de resolución sin transformaciones.

## 4. Módulo de integraciones (extensible)

- **Contrato** (`integrations/base.py`): una integración declara `name`, `supported_events`,
  `handle()` (salida), `verify_inbound()` y `handle_inbound()` (entrada).
- **Registry** (`integrations/__init__.py`): `register/get/all` + `dispatch(event, payload)` que recorre
  las integraciones **activas** (tabla `integrations`) y **aísla fallos** (un error no detiene a las demás;
  todo se registra en `integrations_log`).
- **Eventos de dominio**: `ticket.created`, `ticket.assigned`, `ticket.status_changed`, `ticket.commented`.
- **Entrada**: `POST /trackion/integrations/{name}/webhook` valida firma/secreto y delega a la integración.
- **Agregar una integración nueva** = crear un archivo en `integrations/` y `register(...)`. Cero cambios
  en el núcleo; la activación y config son por datos.

## 5. Seguridad

- Secretos en **SSM Parameter Store** (`/trackion/...`), inyectados como env por `serverless.yml`. Nada en código/YAML.
- Auth: JWT HS256 (PyJWT); passwords con PBKDF2-HMAC-SHA256 (200k iteraciones, salt aleatorio).
- Frontend en S3 **privado**; acceso solo vía CloudFront (OAC). API por HTTPS.
- CI/CD por **OIDC** (rol IAM, sin llaves de larga vida).
- *Develop*: RDS publicly-accessible con TLS. *Prod (pendiente)*: VPC privada + verificación de CA TLS.

## 6. Despliegue

- IaC: `backend/serverless.yml` (CloudFormation). Stack `trackion-<stage>`.
- Stages: `develop` (activo), `staging`/`production` (activar creando SSM `/{stage}/trackion/...`).
- CI/CD: `.github/workflows/deploy.yml` — PR→pytest; push a `main`→package + deploy.
