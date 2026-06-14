## ADDED Requirements

### Requirement: SLA por prioridad

Cada prioridad SHALL definir un objetivo de resolución en horas (`sla_hours`). Los valores base SHALL ser:
`urgente=4`, `alto=6`, `medio=24`, `bajo=48`. El campo SHALL ser administrable como parte del catálogo de prioridades.

#### Scenario: Prioridades con SLA sembrado
- **WHEN** se consultan las prioridades tras inicializar el esquema
- **THEN** cada prioridad incluye su `sla_hours` con los valores base (urgente 4, alto 6, medio 24, bajo 48)

#### Scenario: Actualizar SLA de una prioridad
- **WHEN** un administrador actualiza `sla_hours` de una prioridad a un valor positivo
- **THEN** el sistema lo persiste y los tickets de esa prioridad recalculan su vencimiento

### Requirement: Estado de SLA por ticket

Cada ticket SHALL exponer `sla_due_at` (= `created_at` + `sla_hours` de su prioridad) y `sla_status`
derivado: `met` si se resolvió dentro del plazo, `breached` si venció sin resolver o se resolvió tarde,
`due_soon` si está dentro del 20% final del plazo, `on_track` en otro caso.

#### Scenario: Ticket dentro de plazo
- **WHEN** un ticket abierto no ha superado su `sla_due_at` ni el umbral de "por vencer"
- **THEN** su `sla_status` es `on_track`

#### Scenario: Ticket vencido
- **WHEN** un ticket abierto supera su `sla_due_at`
- **THEN** su `sla_status` es `breached`

#### Scenario: Ticket resuelto a tiempo
- **WHEN** un ticket se marca `resolved` con `resolved_at` anterior o igual a `sla_due_at`
- **THEN** su `sla_status` es `met`
