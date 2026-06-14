"""Servicio y handlers de tickets: CRUD, estados, asignación y comentarios."""
from . import db, integrations
from .http import ApiError, build_response, parse_body, path_param, query_params, require_field, identity

VALID_STATUSES = ("open", "in_progress", "resolved", "closed")
# Transiciones permitidas del ciclo de vida del ticket.
ALLOWED_TRANSITIONS = {
    "open": {"in_progress", "resolved", "closed"},
    "in_progress": {"resolved", "closed", "open"},
    "resolved": {"closed", "in_progress"},
    "closed": set(),
}

_TICKET_SELECT = """
    SELECT t.id, t.subject, t.description, t.status,
           t.category_id, c.name AS category,
           t.subcategory_id, sc.name AS subcategory,
           t.priority_id, p.name AS priority, p.level AS priority_level,
           p.sla_hours,
           t.requester_id, ru.name AS requester,
           t.assignee_id, au.name AS assignee,
           t.created_at, t.updated_at, t.resolved_at,
           (t.created_at + make_interval(hours => p.sla_hours)) AS sla_due_at,
           CASE
             WHEN t.status IN ('resolved', 'closed') THEN
               CASE WHEN t.resolved_at IS NOT NULL
                         AND t.resolved_at <= t.created_at + make_interval(hours => p.sla_hours)
                    THEN 'met' ELSE 'breached' END
             WHEN now() > t.created_at + make_interval(hours => p.sla_hours) THEN 'breached'
             WHEN now() > t.created_at + make_interval(mins => (p.sla_hours * 48)) THEN 'due_soon'
             ELSE 'on_track'
           END AS sla_status
    FROM tickets t
    JOIN categories c ON c.id = t.category_id
    JOIN priorities p ON p.id = t.priority_id
    JOIN users ru ON ru.id = t.requester_id
    LEFT JOIN subcategories sc ON sc.id = t.subcategory_id
    LEFT JOIN users au ON au.id = t.assignee_id
"""


def _current_user_id(event) -> int:
    sub = identity(event).get("sub")
    if sub is None:
        raise ApiError(401, "unauthenticated", "No autenticado")
    return int(sub)


def list_tickets(event):
    q = query_params(event)
    where, params = [], {}
    if q.get("status"):
        where.append("t.status = :status")
        params["status"] = q["status"]
    if q.get("priority"):
        where.append("p.name = :priority")
        params["priority"] = q["priority"]
    if q.get("category"):
        where.append("c.name = :category")
        params["category"] = q["category"]
    if q.get("assignee_id"):
        where.append("t.assignee_id = :assignee_id")
        params["assignee_id"] = int(q["assignee_id"])
    sql = _TICKET_SELECT
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY t.created_at DESC LIMIT 200"
    return build_response(200, {"items": db.query(sql, **params)})


def get_ticket(event):
    tid = int(path_param(event, "id"))
    ticket = db.query_one(_TICKET_SELECT + " WHERE t.id = :id", id=tid)
    if not ticket:
        raise ApiError(404, "not_found", "Ticket no encontrado")
    ticket["comments"] = db.query(
        """SELECT tc.id, tc.body, tc.created_at, tc.author_id, u.name AS author
           FROM ticket_comments tc JOIN users u ON u.id = tc.author_id
           WHERE tc.ticket_id = :id ORDER BY tc.created_at ASC""",
        id=tid,
    )
    return build_response(200, ticket)


def create_ticket(event):
    data = parse_body(event)
    subject = require_field(data, "subject")
    category_id = int(require_field(data, "category_id"))
    priority_id = int(require_field(data, "priority_id"))
    description = data.get("description", "")
    subcategory_id = data.get("subcategory_id")
    requester_id = int(data.get("requester_id") or _current_user_id(event))

    if not db.query_one("SELECT 1 AS ok FROM categories WHERE id = :id AND is_active", id=category_id):
        raise ApiError(400, "invalid_category", "La categoría no existe o está inactiva")
    if not db.query_one("SELECT 1 AS ok FROM priorities WHERE id = :id AND is_active", id=priority_id):
        raise ApiError(400, "invalid_priority", "La prioridad no existe o está inactiva")
    if subcategory_id is not None:
        subcategory_id = int(subcategory_id)
        if not db.query_one(
            "SELECT 1 AS ok FROM subcategories WHERE id = :id AND category_id = :c",
            id=subcategory_id, c=category_id,
        ):
            raise ApiError(400, "invalid_subcategory", "La subcategoría no pertenece a la categoría")

    row = db.execute(
        """INSERT INTO tickets (subject, description, category_id, subcategory_id, priority_id, requester_id)
           VALUES (:s, :d, :c, :sc, :p, :r) RETURNING id""",
        s=subject, d=description, c=category_id, sc=subcategory_id, p=priority_id, r=requester_id,
    )
    ticket = db.query_one(_TICKET_SELECT + " WHERE t.id = :id", id=row[0]["id"])
    integrations.dispatch("ticket.created", ticket)
    return build_response(201, ticket)


def update_ticket(event):
    tid = int(path_param(event, "id"))
    data = parse_body(event)
    current = db.query_one("SELECT status FROM tickets WHERE id = :id", id=tid)
    if not current:
        raise ApiError(404, "not_found", "Ticket no encontrado")

    sets, params = [], {"id": tid}
    for field in ("subject", "description"):
        if field in data:
            sets.append(f"{field} = :{field}")
            params[field] = data[field]
    if "priority_id" in data:
        sets.append("priority_id = :priority_id")
        params["priority_id"] = int(data["priority_id"])

    new_status = data.get("status")
    status_changed = False
    if new_status is not None:
        if new_status not in VALID_STATUSES:
            raise ApiError(400, "invalid_status", f"Estado inválido: {new_status}")
        old = current["status"]
        if new_status != old and new_status not in ALLOWED_TRANSITIONS[old]:
            raise ApiError(400, "invalid_transition", f"Transición no permitida: {old} → {new_status}")
        sets.append("status = :status")
        params["status"] = new_status
        if new_status == "resolved":
            sets.append("resolved_at = now()")
        status_changed = new_status != old

    if not sets:
        raise ApiError(400, "no_changes", "No hay campos para actualizar")
    sets.append("updated_at = now()")
    db.execute(f"UPDATE tickets SET {', '.join(sets)} WHERE id = :id", **params)

    ticket = db.query_one(_TICKET_SELECT + " WHERE t.id = :id", id=tid)
    if status_changed:
        integrations.dispatch("ticket.status_changed", ticket)
    return build_response(200, ticket)


def assign_ticket(event):
    tid = int(path_param(event, "id"))
    data = parse_body(event)
    assignee_id = int(require_field(data, "assignee_id"))
    if not db.query_one("SELECT 1 AS ok FROM tickets WHERE id = :id", id=tid):
        raise ApiError(404, "not_found", "Ticket no encontrado")
    if not db.query_one("SELECT 1 AS ok FROM users WHERE id = :id AND is_active", id=assignee_id):
        raise ApiError(400, "invalid_assignee", "El usuario asignado no existe o está inactivo")
    db.execute(
        "UPDATE tickets SET assignee_id = :a, updated_at = now() WHERE id = :id",
        a=assignee_id, id=tid,
    )
    ticket = db.query_one(_TICKET_SELECT + " WHERE t.id = :id", id=tid)
    integrations.dispatch("ticket.assigned", ticket)
    return build_response(200, ticket)


def list_comments(event):
    tid = int(path_param(event, "id"))
    rows = db.query(
        """SELECT tc.id, tc.body, tc.created_at, tc.author_id, u.name AS author
           FROM ticket_comments tc JOIN users u ON u.id = tc.author_id
           WHERE tc.ticket_id = :id ORDER BY tc.created_at ASC""",
        id=tid,
    )
    return build_response(200, {"items": rows})


def add_comment(event):
    tid = int(path_param(event, "id"))
    data = parse_body(event)
    body = require_field(data, "body")
    if not db.query_one("SELECT 1 AS ok FROM tickets WHERE id = :id", id=tid):
        raise ApiError(404, "not_found", "Ticket no encontrado")
    author_id = _current_user_id(event)
    row = db.execute(
        """INSERT INTO ticket_comments (ticket_id, author_id, body)
           VALUES (:t, :a, :b) RETURNING id, created_at""",
        t=tid, a=author_id, b=body,
    )
    integrations.dispatch("ticket.commented", {"ticket_id": tid, "comment_id": row[0]["id"], "body": body})
    return build_response(201, {"id": row[0]["id"], "ticket_id": tid, "body": body, "created_at": row[0]["created_at"]})
