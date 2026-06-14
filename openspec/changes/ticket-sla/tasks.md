## 0. Preparación

- [x] 0.1 Trabajar sobre el repo local (rama main; cambio acotado)

## 1. SLA por prioridad

- [x] 1.1 `db.py`: columna `priorities.sla_hours` (ALTER ADD COLUMN IF NOT EXISTS) + semilla idempotente
      (urgente=4, alto=6, medio=24, bajo=48; nombres baja/media/alta/urgente mapeados a 48/24/6/4)
- [x] 1.2 `tickets.py`: `sla_hours`, `sla_due_at`, `sla_status` (met/breached/due_soon/on_track) en el SELECT
- [x] 1.3 `catalog.py`: incluir `sla_hours` en list/create/update de prioridades

## 2. Datos de demostración

- [x] 2.1 `backend/scripts/seed_dummy.py`: 20 tickets variados (prioridad, estado, fechas pasadas,
      algunos asignados/resueltos/comentados) + categorías/subcategorías/agentes extra

## 3. Verificación (OBLIGATORIO) — EL AGENTE EJECUTA

- [x] 3.1 `python -m pytest` (sin regresiones) + rebuild del contenedor api
- [x] 3.2 Correr el seed contra la BD local y verificar conteos y distribución de `sla_status`
