## 0. Preparación

- [ ] 0.1 Crear feature branch `feature/helpdesk-mvp` (SIEMPRE PRIMERO)

## 1. Andamiaje del backend

- [ ] 1.1 Crear `backend/serverless.yml` (servicio `trackion`, provider python3.12, región us-east-2, HTTP API base `/trackion`, env desde SSM)
- [ ] 1.2 Crear `backend/requirements.txt` (`pg8000`, `PyJWT`) y vendorizar en `backend/vendor/`
- [ ] 1.3 Crear `backend/handler.py` (carga `vendor` en sys.path, router `(method, path)` → handlers, authorizer)
- [ ] 1.4 Crear `backend/app/config.py` y `backend/app/http.py` (lectura de env, build_response, parse de body/eventos)

## 2. Capa de datos (PostgreSQL)

- [ ] 2.1 `backend/app/db.py`: conexión pg8000, `query()/execute()/tx()` parametrizados
- [ ] 2.2 `ensure_schema()` idempotente con todas las tablas del data model (design.md)
- [ ] 2.3 Semilla: usuario admin, prioridades base, categoría general (idempotente)

## 3. Auth (capability: auth)

- [ ] 3.1 `backend/app/auth.py`: PBKDF2 (hash/verify), emisión/validación JWT
- [ ] 3.2 Handlers `POST /trackion/auth/login`, `GET /trackion/auth/me`
- [ ] 3.3 `authorizer` de API Gateway (valida Bearer JWT)

## 4. Tickets (capability: tickets)

- [ ] 4.1 `backend/app/tickets.py`: servicio CRUD + estados + asignación + comentarios
- [ ] 4.2 Handlers: list/create/detail/update, `assign`, `comments` (GET/POST)
- [ ] 4.3 Emitir eventos de dominio vía `integrations.dispatch()`

## 5. Catálogo (capability: catalog)

- [ ] 5.1 `backend/app/catalog.py`: CRUD de categorías, subcategorías, prioridades y usuarios
- [ ] 5.2 Handlers `/trackion/catalog/*`

## 6. Integraciones (capability: integrations)

- [ ] 6.1 `backend/app/integrations/base.py`: contrato `Integration` (name, events, handle, inbound, verify)
- [ ] 6.2 `backend/app/integrations/__init__.py`: registry (`register/get/all`) + `dispatch()` con aislamiento de fallos + log
- [ ] 6.3 `backend/app/integrations/webhook.py`: integración de ejemplo (webhook genérico de salida + inbound)
- [ ] 6.4 Handlers `GET /trackion/integrations`, `POST /trackion/integrations/{name}/webhook`

## 7. Observabilidad (capability: observability)

- [ ] 7.1 Handler `GET /trackion/health` (público; chequea DB) y `resolved_at` en transición a `resolved`

## 8. Frontend (paleta metálica)

- [ ] 8.1 `frontend/css/style.css` con tokens metálicos; `login.html` + `index.html`
- [ ] 8.2 `frontend/js/{config,api,app}.js`: login, dashboard, lista, detalle, crear/asignar/comentar

## 9. CI/CD

- [ ] 9.1 `.github/workflows/deploy.yml`: PR → pytest + `serverless package`; push a main → deploy a AWS

## N. Revisar y actualizar pruebas existentes (OBLIGATORIO)

- [ ] N.1 Crear `backend/tests/` (pytest): auth (hash/JWT), router, integraciones (registry/dispatch/aislamiento), validaciones de tickets

## N+1. Ejecutar pruebas y verificar estado (OBLIGATORIO) — EL AGENTE EJECUTA

- [ ] N+1.1 Ejecutar `python -m pytest backend/tests` y `serverless package --stage develop`
- [ ] N+1.2 Crear reporte en `openspec/changes/helpdesk-mvp/reports/AAAA-MM-DD-step-N+1-pruebas-y-verificacion.md`

## N+2. Verificación manual según tipo de proyecto (OBLIGATORIO) — EL AGENTE EJECUTA

- [ ] N+2.1 API: tras deploy, `curl` health → login → crear ticket → listar → asignar → comentar; cubrir casos de error (401/400/404); restaurar datos de prueba

## N+3. Actualizar documentación técnica (OBLIGATORIO)

- [ ] N+3.1 Actualizar README, `docs/backend-standards.md`, `docs/ci-cd-standards.md` y el resumen de API si cambió algo durante la implementación
