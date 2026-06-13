## ADDED Requirements

### Requirement: Registry de integraciones extensible

El sistema SHALL mantener un registro de integraciones desacoplado del núcleo, donde cada integración se
identifica por un `name` y se registra sin modificar la lógica de dominio. Agregar una integración nueva
SHALL requerir únicamente crear su archivo y registrarla.

#### Scenario: Listar integraciones disponibles
- **WHEN** un administrador llama `GET /trackion/integrations`
- **THEN** el sistema devuelve las integraciones registradas con su `name`, descripción y estado (activa/inactiva)

#### Scenario: Integración inexistente
- **WHEN** se referencia una integración cuyo `name` no está registrado
- **THEN** el sistema responde 404 y no ejecuta ninguna acción

### Requirement: Dispatch de eventos de dominio a integraciones de salida

El sistema SHALL emitir eventos de dominio (`ticket.created`, `ticket.assigned`, `ticket.status_changed`,
`ticket.commented`) y entregarlos a las integraciones activas mediante el módulo de integraciones. Un fallo
de una integración NO SHALL interrumpir la operación de negocio ni el dispatch a las demás.

#### Scenario: Entrega a integración activa
- **WHEN** se crea un ticket y existe una integración de salida activa suscrita a `ticket.created`
- **THEN** el módulo invoca a la integración con el evento y el payload del ticket, y registra el resultado

#### Scenario: Aislamiento de fallos
- **WHEN** una integración activa lanza un error al manejar un evento
- **THEN** el sistema registra el error, continúa con las demás integraciones y la operación de negocio se completa

### Requirement: Webhooks de entrada genéricos

El sistema SHALL exponer un endpoint genérico de entrada `POST /trackion/integrations/{name}/webhook` que
enrute el payload al handler de entrada de la integración indicada, validando su secreto/firma cuando aplique.

#### Scenario: Webhook entrante válido
- **WHEN** llega `POST /trackion/integrations/{name}/webhook` con firma/secreto válido para una integración registrada
- **THEN** el sistema delega el payload al handler de entrada de esa integración y responde 200

#### Scenario: Webhook con firma inválida
- **WHEN** llega un webhook con firma/secreto inválido
- **THEN** el sistema responde 401 y no procesa el payload
