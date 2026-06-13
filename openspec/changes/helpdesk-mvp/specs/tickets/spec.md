## ADDED Requirements

### Requirement: Creación de tickets

El sistema SHALL permitir crear un ticket con asunto, descripción, categoría, subcategoría (opcional),
prioridad y solicitante. Al crearse, el ticket SHALL quedar en estado `open` con marca de tiempo.

#### Scenario: Creación válida
- **WHEN** un usuario autenticado envía `POST /trackion/tickets` con asunto, descripción, categoría y prioridad válidas
- **THEN** el sistema crea el ticket en estado `open`, devuelve 201 con el ticket y emite el evento `ticket.created`

#### Scenario: Datos faltantes o inválidos
- **WHEN** falta el asunto, o la categoría/prioridad no existe
- **THEN** el sistema responde 400 con el detalle del campo inválido y no crea el ticket

### Requirement: Listado y consulta de tickets

El sistema SHALL listar tickets con filtros por estado, prioridad, categoría y asignado, y SHALL permitir
ver el detalle de un ticket por id.

#### Scenario: Listado con filtro
- **WHEN** se llama `GET /trackion/tickets?status=open&priority=alta`
- **THEN** el sistema devuelve solo los tickets que cumplen ambos filtros, ordenados por fecha descendente

#### Scenario: Detalle existente
- **WHEN** se llama `GET /trackion/tickets/{id}` con un id existente
- **THEN** el sistema devuelve el ticket con su categoría, prioridad, asignado y comentarios

#### Scenario: Detalle inexistente
- **WHEN** se llama `GET /trackion/tickets/{id}` con un id que no existe
- **THEN** el sistema responde 404

### Requirement: Cambio de estado y asignación

El sistema SHALL permitir actualizar el estado de un ticket dentro del flujo
`open → in_progress → resolved → closed` y asignarlo a un usuario/agente.

#### Scenario: Asignación
- **WHEN** se llama `POST /trackion/tickets/{id}/assign` con un usuario válido
- **THEN** el ticket queda asignado a ese usuario, se actualiza `updated_at` y se emite `ticket.assigned`

#### Scenario: Transición de estado válida
- **WHEN** se actualiza el estado de un ticket `open` a `in_progress`
- **THEN** el sistema acepta el cambio, lo registra y emite `ticket.status_changed`

#### Scenario: Transición no permitida
- **WHEN** se intenta pasar un ticket `closed` de vuelta a `open`
- **THEN** el sistema responde 400 y conserva el estado anterior

### Requirement: Comentarios de ticket

El sistema SHALL permitir agregar comentarios a un ticket y listarlos en orden cronológico.

#### Scenario: Comentario agregado
- **WHEN** un usuario autenticado envía `POST /trackion/tickets/{id}/comments` con un cuerpo no vacío
- **THEN** el sistema guarda el comentario con autor y fecha, responde 201 y emite `ticket.commented`
