# Trackion — mesa de ayuda serverless con integraciones abiertas

> **Estado:** MVP en construcción (stage `develop`). Helpdesk propio, white-label, sin acoplarse a
> ningún proveedor externo de tickets. Flujo de desarrollo: **Spec-Driven Development (OpenSpec)**.

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

Detalle por capa en [docs/backend-standards.md](docs/backend-standards.md).

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

## 🚀 Configuración (quickstart)

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

## 🔄 Cómo contribuir (SDD)

**Spec-first**: nada de código antes de su spec. Por cada cambio:
`feature/[change]` → `proposal → specs → design → tasks` (con `/opsx:*`) → implementar → `verify` →
PR → `archive`. Ver [docs/ci-cd-standards.md](docs/ci-cd-standards.md).

A partir del **segundo push**, el despliegue es automático (GitHub Actions → AWS); el primer push y el
primer deploy son manuales.

## 📄 Licencia

MIT (ver `LICENSE`).
