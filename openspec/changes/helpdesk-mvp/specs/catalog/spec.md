## ADDED Requirements

### Requirement: Administración de categorías y subcategorías

El sistema SHALL permitir crear, listar, actualizar y desactivar categorías y subcategorías. Cada
subcategoría SHALL pertenecer a una categoría.

#### Scenario: Crear categoría
- **WHEN** un administrador envía `POST /trackion/catalog/categories` con un nombre único
- **THEN** el sistema crea la categoría activa y responde 201

#### Scenario: Subcategoría con categoría inválida
- **WHEN** se crea una subcategoría referenciando una categoría inexistente
- **THEN** el sistema responde 400 y no la crea

### Requirement: Administración de prioridades

El sistema SHALL permitir administrar prioridades con nombre y nivel (orden), usadas al clasificar tickets.

#### Scenario: Listar prioridades
- **WHEN** se llama `GET /trackion/catalog/priorities`
- **THEN** el sistema devuelve las prioridades activas ordenadas por nivel

### Requirement: Administración de usuarios

El sistema SHALL permitir administrar usuarios/agentes (alta, listado, actualización, baja lógica) con rol
(`admin` | `agent` | `requester`) y estado activo/inactivo. La contraseña SHALL guardarse con PBKDF2.

#### Scenario: Alta de usuario
- **WHEN** un administrador crea un usuario con email único, nombre, rol y contraseña
- **THEN** el sistema lo crea activo, almacena la contraseña con PBKDF2 y responde 201 sin devolver el hash

#### Scenario: Email duplicado
- **WHEN** se intenta crear un usuario con un email ya registrado
- **THEN** el sistema responde 409 y no crea el usuario
