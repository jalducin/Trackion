> Estado: implementado y verificado el 2026-06-13. Ver `reports/2026-06-13-step-N+1-pruebas-y-verificacion.md`.

## 0. Preparación

- [x] 0.1 Crear feature branch `feature/helpdesk-mvp` (SIEMPRE PRIMERO)

## 1. Andamiaje del backend

- [x] 1.1 `backend/serverless.yml` (servicio `trackion`, python3.12, us-east-2, HTTP API base `/trackion`, env desde SSM)
- [x] 1.2 `backend/requirements.txt` (`pg8000`, `PyJWT`) vendorizado en `backend/vendor/`
- [x] 1.3 `backend/handler.py` (vendor en sys.path, router `(method, path)` → handlers, authorizer)
- [x] 1.4 `backend/app/config.py` y `backend/app/http.py`

## 2. Capa de datos (PostgreSQL)

- [x] 2.1 `backend/app/db.py`: conexión pg8000, `query()/execute()` parametrizados
- [x] 2.2 `ensure_schema()` idempotente con todas las tablas del data model
- [x] 2.3 Semilla: usuario admin, prioridades base, categoría general (idempotente)

## 3. Auth (capability: auth)

- [x] 3.1 PBKDF2 (hash/verify), emisión/validación JWT
- [x] 3.2 Handlers `POST /trackion/auth/login`, `GET /trackion/auth/me`
- [x] 3.3 `authorizer` de API Gateway

## 4. Tickets (capability: tickets)

- [x] 4.1 Servicio CRUD + estados + asignación + comentarios
- [x] 4.2 Handlers: list/create/detail/update, `assign`, `comments`
- [x] 4.3 Emisión de eventos de dominio vía `integrations.dispatch()`

## 5. Catálogo (capability: catalog)

- [x] 5.1 CRUD de categorías, subcategorías, prioridades y usuarios
- [x] 5.2 Handlers `/trackion/catalog/*`

## 6. Integraciones (capability: integrations)

- [x] 6.1 `integrations/base.py`: contrato `Integration`
- [x] 6.2 `integrations/__init__.py`: registry + `dispatch()` con aislamiento de fallos + log
- [x] 6.3 `integrations/webhook.py`: integración de ejemplo (salida + inbound)
- [x] 6.4 Handlers `GET /trackion/integrations`, `POST /trackion/integrations/{name}/webhook`

## 7. Observabilidad (capability: observability)

- [x] 7.1 `GET /trackion/health` (público; chequea DB) y `resolved_at` en transición a `resolved`

## 8. Frontend (paleta metálica)

- [x] 8.1 `frontend/css/style.css` con tokens metálicos; `login.html` + `index.html`
- [x] 8.2 `frontend/js/{config,api,app}.js`: login, dashboard, lista, detalle, crear/asignar/comentar

## 9. CI/CD

- [x] 9.1 `.github/workflows/deploy.yml`: PR → pytest; push a main → package + deploy a AWS

## N. Revisar y actualizar pruebas existentes (OBLIGATORIO)

- [x] N.1 `backend/tests/` (pytest): auth, router/http, integraciones — 18 pruebas

## N+1. Ejecutar pruebas y verificar estado (OBLIGATORIO)

- [x] N+1.1 `python -m pytest` (18/18) y `serverless package --stage develop` (OK)
- [x] N+1.2 Reporte en `reports/2026-06-13-step-N+1-pruebas-y-verificacion.md`

## N+2. Verificación manual (OBLIGATORIO)

- [x] N+2.1 API desplegada: health→login→crear→listar→asignar→comentar + casos de error; estado restaurado

## N+3. Actualizar documentación técnica (OBLIGATORIO)

- [x] N+3.1 README, estándares y endpoint del frontend (`config.js`) actualizados
