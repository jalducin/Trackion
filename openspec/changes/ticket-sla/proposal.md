## Why

Operación de soporte necesita compromisos de tiempo de resolución (SLA) por prioridad para priorizar y
medir cumplimiento. Sin SLA no hay forma de saber qué tickets están por incumplir ni de graficarlo en Grafana.

## What Changes

- Cada **prioridad** define un SLA en horas: `urgente=4`, `alto=6`, `medio=24`, `bajo=48`.
- Cada **ticket** expone `sla_hours`, `sla_due_at` (= `created_at` + SLA) y `sla_status`
  (`on_track` | `due_soon` | `breached` | `met`), calculado en la capa de datos.
- Datos de demostración: script que genera **20 tickets dummy** variados (prioridad, estado, fechas)
  para poblar estados de SLA y tableros de Grafana.

## Capabilities

### New Capabilities
- `sla`: compromisos de tiempo de resolución por prioridad y estado de cumplimiento por ticket.

### Modified Capabilities
- (ninguna archivada aún; se integra con `tickets` y `catalog` del cambio helpdesk-mvp)

## Impact

- `backend/app/db.py`: columna `priorities.sla_hours` (aditiva, idempotente) + semilla de valores.
- `backend/app/tickets.py`: `sla_due_at` y `sla_status` en el SELECT de tickets.
- `backend/app/catalog.py`: `sla_hours` en respuestas de prioridades.
- `backend/scripts/seed_dummy.py`: generador de 20 tickets de demostración.
