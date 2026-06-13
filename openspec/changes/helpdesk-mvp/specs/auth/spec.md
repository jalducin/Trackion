## ADDED Requirements

### Requirement: Autenticación por credenciales

El sistema SHALL permitir a un usuario autenticarse con email y contraseña y, si son válidos, emitir un
token JWT firmado con expiración. Las contraseñas SHALL almacenarse con PBKDF2 (sin texto plano).

#### Scenario: Login exitoso
- **WHEN** un usuario activo envía `POST /trackion/auth/login` con email y contraseña correctos
- **THEN** el sistema responde 200 con un JWT válido y los datos públicos del usuario (id, nombre, rol)

#### Scenario: Credenciales inválidas
- **WHEN** se envía un email inexistente o una contraseña incorrecta
- **THEN** el sistema responde 401 sin revelar cuál de los dos campos falló

#### Scenario: Usuario inactivo
- **WHEN** un usuario marcado como inactivo intenta autenticarse con credenciales correctas
- **THEN** el sistema responde 403 y no emite token

### Requirement: Validación de identidad en rutas protegidas

El sistema SHALL exigir un JWT válido (header `Authorization: Bearer`) para acceder a rutas protegidas y
SHALL exponer la identidad del usuario autenticado vía `GET /trackion/auth/me`.

#### Scenario: Token válido
- **WHEN** se llama una ruta protegida con un JWT vigente y bien firmado
- **THEN** el sistema procesa la petición con la identidad del token

#### Scenario: Token ausente o inválido
- **WHEN** se llama una ruta protegida sin token, con token expirado o con firma inválida
- **THEN** el sistema responde 401 y no ejecuta la operación
