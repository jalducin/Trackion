"""Servicio y handlers de catálogo: categorías, subcategorías, prioridades y usuarios."""
from . import auth, db
from .http import ApiError, build_response, parse_body, path_param, require_field


# ── Categorías ──

def list_categories(event):
    return build_response(200, {"items": db.query(
        "SELECT id, name, is_active, created_at FROM categories ORDER BY name")})


def create_category(event):
    name = require_field(parse_body(event), "name")
    if db.query_one("SELECT 1 AS ok FROM categories WHERE lower(name) = lower(:n)", n=name):
        raise ApiError(409, "duplicate", "La categoría ya existe")
    row = db.execute("INSERT INTO categories (name) VALUES (:n) RETURNING id, name, is_active, created_at", n=name)
    return build_response(201, row[0])


def update_category(event):
    cid = int(path_param(event, "id"))
    data = parse_body(event)
    sets, params = [], {"id": cid}
    if "name" in data:
        sets.append("name = :name"); params["name"] = data["name"]
    if "is_active" in data:
        sets.append("is_active = :is_active"); params["is_active"] = bool(data["is_active"])
    if not sets:
        raise ApiError(400, "no_changes", "No hay campos para actualizar")
    row = db.execute(f"UPDATE categories SET {', '.join(sets)} WHERE id = :id RETURNING id, name, is_active", **params)
    if not row:
        raise ApiError(404, "not_found", "Categoría no encontrada")
    return build_response(200, row[0])


# ── Subcategorías ──

def list_subcategories(event):
    return build_response(200, {"items": db.query(
        """SELECT sc.id, sc.name, sc.category_id, c.name AS category, sc.is_active
           FROM subcategories sc JOIN categories c ON c.id = sc.category_id ORDER BY c.name, sc.name""")})


def create_subcategory(event):
    data = parse_body(event)
    name = require_field(data, "name")
    category_id = int(require_field(data, "category_id"))
    if not db.query_one("SELECT 1 AS ok FROM categories WHERE id = :id", id=category_id):
        raise ApiError(400, "invalid_category", "La categoría no existe")
    row = db.execute(
        "INSERT INTO subcategories (name, category_id) VALUES (:n, :c) RETURNING id, name, category_id, is_active",
        n=name, c=category_id)
    return build_response(201, row[0])


def update_subcategory(event):
    sid = int(path_param(event, "id"))
    data = parse_body(event)
    sets, params = [], {"id": sid}
    if "name" in data:
        sets.append("name = :name"); params["name"] = data["name"]
    if "is_active" in data:
        sets.append("is_active = :is_active"); params["is_active"] = bool(data["is_active"])
    if not sets:
        raise ApiError(400, "no_changes", "No hay campos para actualizar")
    row = db.execute(f"UPDATE subcategories SET {', '.join(sets)} WHERE id = :id RETURNING id, name, is_active", **params)
    if not row:
        raise ApiError(404, "not_found", "Subcategoría no encontrada")
    return build_response(200, row[0])


# ── Prioridades ──

def list_priorities(event):
    return build_response(200, {"items": db.query(
        "SELECT id, name, level, sla_hours, is_active FROM priorities WHERE is_active ORDER BY level")})


def create_priority(event):
    data = parse_body(event)
    name = require_field(data, "name")
    level = int(data.get("level", 0))
    sla_hours = int(data.get("sla_hours", 24))
    if db.query_one("SELECT 1 AS ok FROM priorities WHERE lower(name) = lower(:n)", n=name):
        raise ApiError(409, "duplicate", "La prioridad ya existe")
    row = db.execute(
        "INSERT INTO priorities (name, level, sla_hours) VALUES (:n, :l, :s) RETURNING id, name, level, sla_hours, is_active",
        n=name, l=level, s=sla_hours)
    return build_response(201, row[0])


def update_priority(event):
    pid = int(path_param(event, "id"))
    data = parse_body(event)
    sets, params = [], {"id": pid}
    if "name" in data:
        sets.append("name = :name"); params["name"] = data["name"]
    if "level" in data:
        sets.append("level = :level"); params["level"] = int(data["level"])
    if "sla_hours" in data:
        sets.append("sla_hours = :sla_hours"); params["sla_hours"] = int(data["sla_hours"])
    if "is_active" in data:
        sets.append("is_active = :is_active"); params["is_active"] = bool(data["is_active"])
    if not sets:
        raise ApiError(400, "no_changes", "No hay campos para actualizar")
    row = db.execute(f"UPDATE priorities SET {', '.join(sets)} WHERE id = :id RETURNING id, name, level, sla_hours, is_active", **params)
    if not row:
        raise ApiError(404, "not_found", "Prioridad no encontrada")
    return build_response(200, row[0])


# ── Usuarios ──

def list_users(event):
    return build_response(200, {"items": db.query(
        "SELECT id, email, name, role, is_active, created_at FROM users ORDER BY name")})


def create_user(event):
    data = parse_body(event)
    email = require_field(data, "email")
    name = require_field(data, "name")
    password = require_field(data, "password")
    role = data.get("role", "agent")
    if role not in ("admin", "agent", "requester"):
        raise ApiError(400, "invalid_role", "Rol inválido")
    if db.query_one("SELECT 1 AS ok FROM users WHERE lower(email) = lower(:e)", e=email):
        raise ApiError(409, "duplicate", "El email ya está registrado")
    salt, pwd_hash = auth.hash_password(password)
    row = db.execute(
        """INSERT INTO users (email, name, role, password_hash, password_salt)
           VALUES (:e, :n, :r, :h, :s) RETURNING id, email, name, role, is_active, created_at""",
        e=email, n=name, r=role, h=pwd_hash, s=salt)
    return build_response(201, row[0])


def update_user(event):
    uid = int(path_param(event, "id"))
    data = parse_body(event)
    sets, params = [], {"id": uid}
    if "name" in data:
        sets.append("name = :name"); params["name"] = data["name"]
    if "role" in data:
        if data["role"] not in ("admin", "agent", "requester"):
            raise ApiError(400, "invalid_role", "Rol inválido")
        sets.append("role = :role"); params["role"] = data["role"]
    if "is_active" in data:
        sets.append("is_active = :is_active"); params["is_active"] = bool(data["is_active"])
    if "password" in data and data["password"]:
        salt, pwd_hash = auth.hash_password(data["password"])
        sets.append("password_hash = :h"); params["h"] = pwd_hash
        sets.append("password_salt = :s"); params["s"] = salt
    if not sets:
        raise ApiError(400, "no_changes", "No hay campos para actualizar")
    sets.append("updated_at = now()")
    row = db.execute(f"UPDATE users SET {', '.join(sets)} WHERE id = :id RETURNING id, email, name, role, is_active", **params)
    if not row:
        raise ApiError(404, "not_found", "Usuario no encontrado")
    return build_response(200, row[0])
