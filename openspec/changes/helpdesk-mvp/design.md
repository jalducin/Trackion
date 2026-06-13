## Context

Trackion arranca como proyecto nuevo. Se decidió un helpdesk propio (no rebrand del backend legacy de
soporte) sobre infraestructura serverless aislada en la cuenta AWS `957266312835`, región `us-east-2`.
El repositorio será **público**, por lo que ningún secreto ni código interno legacy puede publicarse.
Monitoreo previsto con **Grafana** sobre PostgreSQL.

## Goals / Non-Goals

**Goals:**
- API serverless desplegable (`trackion-develop`) con auth JWT, tickets, catálogo, integraciones y health.
- Módulo de integraciones **extensible** (alta de integraciones sin tocar el núcleo).
- Esquema PostgreSQL idempotente y apto para Grafana.
- Solo dependencias puras-Python (sin build nativo / sin Docker).
- Frontend SPA vanilla con paleta metálica.

**Non-Goals:**
- Integraciones concretas con Freshdesk/Asana/WhatsApp (queda solo el ejemplo de webhook genérico).
- SSO/Google OAuth (auth local por ahora).
- Multi-tenant / RLS (futuro).
- Alta disponibilidad multi-AZ / VPC privada (develop usa conexión directa).

## Decisions

- **pg8000 en vez de psycopg2.** Driver PostgreSQL puro-Python → empaquetable sin Docker en Lambda.
  Alternativa psycopg2-binary descartada por requerir wheels nativos manylinux.
- **Vendorizar deps en `backend/vendor/`** y agregarlas a `sys.path` desde `handler.py`.
  Alternativa Lambda Layer propia descartada para el MVP (más pasos de release); se puede migrar luego.
- **PBKDF2 (hashlib) en vez de bcrypt.** Evita dependencia nativa; suficiente con iteraciones altas + salt.
- **Una sola Lambda `api` con router interno** + Lambda `authorizer`. Menos recursos y cold paths que una
  función por endpoint; el router mapea `(method, path)` a handlers de capa. Se puede dividir si crece.
- **Integraciones por datos + registry en código.** El registry (`integrations/__init__.py`) descubre las
  clases registradas; la tabla `integrations` define cuáles están activas y su config (secreto, url, eventos).
  `dispatch(event, payload)` aísla fallos por integración (try/except + log en `integrations_log`).
- **Esquema idempotente `ensure_schema()`** ejecutado en cold start: `CREATE TABLE IF NOT EXISTS` +
  `ALTER ... ADD COLUMN IF NOT EXISTS`. Semilla: usuario admin, prioridades base, categoría general.
- **Secrets en SSM** `/trackion/...`, inyectados como env por `serverless.yml` (`${ssm:...}`).
- **CORS** gestionado por API Gateway; orígenes configurables por stage.

## Data model (PostgreSQL)

```
users(id, email[unique], name, role, password_hash, password_salt, is_active, created_at, updated_at)
categories(id, name[unique], is_active, created_at)
subcategories(id, category_id→categories, name, is_active, created_at)
priorities(id, name[unique], level[int], is_active)
tickets(id, subject, description, category_id→categories, subcategory_id→subcategories NULL,
        priority_id→priorities, status[open|in_progress|resolved|closed], requester_id→users,
        assignee_id→users NULL, created_at, updated_at, resolved_at NULL)
ticket_comments(id, ticket_id→tickets, author_id→users, body, created_at)
integrations(id, name[unique], is_active, config[jsonb], events[text[]], created_at, updated_at)
integrations_log(id, integration_name, event, status, detail, created_at)
```

## Risks / Trade-offs

- [Conectividad Lambda↔PostgreSQL] → develop usa Postgres alcanzable públicamente con TLS; en
  staging/prod migrar a VPC + security groups.
- [Cold start con ensure_schema] → barato (IF NOT EXISTS); se ejecuta una vez por contenedor.
- [Repo público filtrando datos] → `reference/`, `vendor/`, `.env` en `.gitignore`; secrets solo en SSM/Actions.
- [Una sola Lambda] → acoplamiento de despliegue; mitigado porque el router está separado por módulos.
- [PBKDF2 vs bcrypt] → aceptable con iteraciones ≥ 200k; documentado para revisión futura.

## Migration Plan

1. Crear SSM `/trackion/...` (DB + jwt secret).
2. `serverless deploy --stage develop` (crea API GW, Lambdas, authorizer).
3. Cold start ejecuta `ensure_schema()` + semilla; verificar `/trackion/health`.
4. Rollback: `serverless remove --stage develop` (servicio aislado, no afecta a soporte).

## Open Questions

- Endpoint/credenciales definitivos de PostgreSQL para `develop` (decisión de provisión de BD).
- Estrategia de credenciales en CI: secrets de repo vs OIDC (recomendado OIDC).
