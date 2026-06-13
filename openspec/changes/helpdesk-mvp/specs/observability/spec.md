## ADDED Requirements

### Requirement: Endpoint de salud

El sistema SHALL exponer `GET /trackion/health` (público, sin autenticación) que reporte el estado del
servicio y la conectividad con la base de datos.

#### Scenario: Servicio sano
- **WHEN** se llama `GET /trackion/health` y la base de datos responde
- **THEN** el sistema responde 200 con `{ "status": "ok", "db": "up", "version": <str> }`

#### Scenario: Base de datos inaccesible
- **WHEN** la base de datos no responde
- **THEN** el sistema responde 503 con `{ "status": "degraded", "db": "down" }`

### Requirement: Modelo de datos apto para Grafana

El esquema PostgreSQL SHALL exponer campos normalizados para monitoreo: marcas de tiempo
(`created_at`, `updated_at`, `resolved_at`), estado y prioridad como valores discretos, de modo que
Grafana pueda graficar volumen, tiempos de resolución y backlog sin transformaciones complejas.

#### Scenario: Consulta de métricas por estado
- **WHEN** Grafana consulta el conteo de tickets agrupado por `status` y día (`created_at`)
- **THEN** la consulta retorna series temporales consistentes sin requerir lógica fuera de SQL

#### Scenario: Tiempo de resolución
- **WHEN** un ticket pasa a `resolved`
- **THEN** el sistema registra `resolved_at`, permitiendo calcular el tiempo de resolución por ticket
