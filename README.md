# Trackion — mesa de ayuda serverless con integraciones abiertas

> **Estado:** MVP funcional, **local-first con Docker** (sin costos de nube). La IaC para AWS sigue
> intacta y el deploy a la nube es opcional/manual. Flujo de desarrollo: **Spec-Driven Development (OpenSpec)**.

> **Arrancar en 1 comando:** `docker compose up --build` → frontend en http://localhost:8081,
> API en http://localhost:8080/trackion. Detalle en [🐳 Local con Docker](#-local-con-docker-sin-aws-costo-0)
> y arquitectura en [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## 🎯 Qué resuelve

Gestión de tickets de soporte de punta a punta:

- Levantar, **categorizar** (categoría/subcategoría), **priorizar**, **asignar** y dar seguimiento a tickets.
- Comentarios e historial por ticket; estados (`open → in_progress → resolved → closed`).
- Catálogos administrables: categorías, subcategorías, prioridades y usuarios/agentes.
- **Módulo de integración de APIs abierto**: conecta cualquier sistema externo sin tocar el núcleo
  (salida vía dispatch de eventos de dominio; entrada vía webhooks genéricos).
- **Monitoreo con Grafana** directamente sobre PostgreSQL.

## 🏗️ Arquitectura

```
┌──────────────────────────────────────────────────────────────────┐
│  CLIENTE — navegador (SPA vanilla, paleta metálica)                │
│  HTML · CSS · JS · fetch (Authorization: Bearer)                   │
└──────────────────────────────────────────────────────────────────┘
                    │  HTTPS  (REST /trackion/*)
                    ▼
┌──────────────────────────────────────────────────────────────────┐
│  API Gateway HTTP API  ·  authorizer JWT                           │
├──────────────────────────────────────────────────────────────────┤
│  AWS Lambda  trackion-api  (router → handlers por capa)            │
│  ┌────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────────────────┐ │
│  │ auth   │ │ tickets  │ │ catalog  │ │ integrations (registry) │ │
│  └────────┘ └──────────┘ └──────────┘ └─────────────────────────┘ │
├──────────────────────────────────────────────────────────────────┤
│  Capa de datos (pg8000, SQL parametrizado, schema idempotente)     │
└──────────────────────────────────────────────────────────────────┘
                    │
                    ▼
        PostgreSQL  ───►  Grafana (monitoreo)
```

Detalle por capa en [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) y [docs/backend-standards.md](docs/backend-standards.md).

## 🛠️ Tecnologías

| Capa | Tecnología |
|------|-----------|
| Runtime | Python 3.12 |
| IaC | Serverless Framework v3 |
| Compute | AWS Lambda |
| HTTP | API Gateway V2 (HTTP API), base path `/trackion` |
| Base de datos | PostgreSQL (driver puro-Python `pg8000`) |
| Auth | JWT (PyJWT) + PBKDF2 (stdlib) |
| Secrets | SSM Parameter Store (`/trackion/...`) |
| Monitoreo | Grafana sobre PostgreSQL + `/trackion/health` |
| Frontend | HTML/CSS/JS vanilla (paleta metálica) |
| CI/CD | GitHub Actions → AWS |

## 📦 Requisitos

- Python 3.12, Node ≥ 18 (para Serverless Framework v3), AWS CLI configurado.
- `serverless` v3 (`npm i -g serverless`).
- Una instancia PostgreSQL alcanzable desde el Lambda (ver `docs/backend-standards.md`).

## 🐳 Local con Docker (sin AWS, costo $0)

Levanta todo el stack —PostgreSQL + API + frontend— en tu máquina:

```bash
cp .env.example .env        # ajusta credenciales locales si quieres
docker compose up --build   # construye y levanta db + api + web
```

- Frontend: http://localhost:8081  · API: http://localhost:8080/trackion  · health: `/health`
- Admin por defecto: `admin@trackion.local` / `admin123` (configurable en `.env`)
- El backend corre los **mismos handlers** que en AWS vía un adaptador HTTP local (`backend/local_server.py`).
- Apagar: `docker compose down` (datos persisten en el volumen `pgdata`; `down -v` los borra).

## 🚀 Configuración (quickstart en AWS)

```bash
# 1) Backend: vendorizar deps puras-python
cd backend
python -m pip install -r requirements.txt -t vendor

# 2) Cargar secretos en SSM (no en código)
#    /trackion/database/{host,port,name,user,password}, /trackion/jwt/secret_key, ...

# 3) Validar empaquetado y desplegar
serverless package --stage develop
serverless deploy  --stage develop

# 4) Frontend: apuntar js/config.js al endpoint y servir estático
cd ../frontend && python -m http.server 8080
```

## 📁 Estructura

```
trackion/
├── backend/        # Lambda Python serverless (API, datos, integraciones)
├── frontend/       # SPA vanilla (paleta metálica)
├── openspec/       # specs SDD (fuente de verdad)
├── docs/           # estándares (base, backend, frontend, ci-cd)
├── .github/        # CI/CD (GitHub Actions → AWS)
├── ai-specs/       # agentes y skills (fuente canónica)
└── reference/      # material de referencia (NO se publica — .gitignore)
```

## 🔗 API (resumen)

`/trackion/health` · `/trackion/auth/login` · `/trackion/auth/me` ·
`/trackion/tickets` (GET/POST) · `/trackion/tickets/{id}` (GET/PUT) ·
`/trackion/tickets/{id}/assign` · `/trackion/tickets/{id}/comments` ·
`/trackion/catalog/{categories|subcategories|priorities|users}` ·
`/trackion/integrations` · `/trackion/integrations/{name}/webhook`.

## 📈 Monitoreo (Grafana)

El monitoreo vive en el proyecto **Monitoreo-Cloud** (Grafana self-hosted), que lee directamente el
PostgreSQL de Trackion:

- **Dashboard** "Trackion — Tickets & SLA" (uid `trackion-tickets`): totales, SLA vencido / por vencer,
  tickets por estado y prioridad, estado de SLA (donut), creados por día y tabla de vencidos.
- **Alerta** "Trackion - SLA vencido" (dispara si hay tickets con SLA vencido > 0 por 5 min).
- **SLA por prioridad:** urgente 4 h · alto 6 h · medio 24 h · bajo 48 h (ver capability `sla`).
- **Datasource** `trackionpg` → contenedor `trackion-db-1`. Como Grafana corre en otro stack/red Docker,
  conectarlo a la red de Trackion: `docker network connect trackion_default grafana`.

> El dashboard, el datasource y la alerta están versionados en `Monitoreo-Cloud/grafana/provisioning/`.

## 🔄 Cómo contribuir (SDD)

**Spec-first**: nada de código antes de su spec. Por cada cambio:
`feature/[change]` → `proposal → specs → design → tasks` (con `/opsx:*`) → implementar → `verify` →
PR → `archive`. Ver [docs/ci-cd-standards.md](docs/ci-cd-standards.md).

A partir del **segundo push**, el despliegue es automático (GitHub Actions → AWS); el primer push y el
primer deploy son manuales.

## 📄 Licencia

MIT (ver `LICENSE`).
