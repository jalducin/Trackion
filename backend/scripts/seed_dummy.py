"""Genera datos de demostración para Trackion: catálogo extra + 20 tickets dummy variados.

Crea tickets con prioridades, estados y fechas de creación distintas para poblar los estados de SLA
(on_track / due_soon / breached / met) y los tableros de Grafana.

Uso (con el stack Docker arriba):
    DB_HOST=localhost DB_PASSWORD=trackion DB_SSL=false python backend/scripts/seed_dummy.py
"""
import os
import sys

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _BACKEND)
sys.path.insert(0, os.path.join(_BACKEND, "vendor"))

from app import db  # noqa: E402

CATEGORIES = ["General", "Acceso", "Facturación", "Infraestructura", "App Móvil"]
SUBCATEGORIES = {
    "Acceso": ["Restablecer contraseña", "Permisos"],
    "Facturación": ["Factura incorrecta", "Pago no aplicado"],
    "Infraestructura": ["Caída de servicio", "Lentitud"],
    "App Móvil": ["Crash", "Sincronización"],
}
AGENTS = [
    ("ana.torres@trackion.local", "Ana Torres"),
    ("luis.mora@trackion.local", "Luis Mora"),
    ("sofia.reyes@trackion.local", "Sofía Reyes"),
]

# (asunto, categoría, prioridad, estado, horas_desde_creación, horas_hasta_resolución|None)
TICKETS = [
    ("No puedo iniciar sesión en el portal", "Acceso", "urgente", "open", 6, None),            # breached (sla 4)
    ("Caída total del servicio de pagos", "Infraestructura", "urgente", "in_progress", 2, None),# on_track/due_soon
    ("La app se cierra al abrir reportes", "App Móvil", "alta", "open", 8, None),               # breached (sla 6)
    ("Factura con monto duplicado", "Facturación", "alta", "in_progress", 3, None),             # on_track
    ("Lentitud al cargar el dashboard", "Infraestructura", "media", "open", 20, None),          # due_soon (sla 24)
    ("Solicitud de permisos de admin", "Acceso", "media", "open", 5, None),                     # on_track
    ("Error de sincronización en móvil", "App Móvil", "baja", "open", 10, None),                # on_track (sla 48)
    ("Consulta general sobre el servicio", "General", "baja", "open", 50, None),                # breached (sla 48)
    ("Pago no aplicado a mi cuenta", "Facturación", "alta", "resolved", 10, 4),                 # met (4<=6)
    ("Restablecer contraseña olvidada", "Acceso", "media", "resolved", 30, 20),                 # met (20<=24)
    ("Servicio intermitente en API", "Infraestructura", "urgente", "resolved", 12, 6),          # breached (6>4)
    ("Crash al subir adjuntos grandes", "App Móvil", "alta", "closed", 40, 5),                  # met
    ("No llega el correo de verificación", "Acceso", "media", "open", 1, None),                 # on_track
    ("Cargo desconocido en la factura", "Facturación", "media", "in_progress", 22, None),       # due_soon
    ("Dashboard no muestra gráficas", "General", "baja", "open", 12, None),                     # on_track
    ("Timeout al exportar a Excel", "Infraestructura", "alta", "open", 7, None),                # breached (>6)
    ("Permisos insuficientes para reporte", "Acceso", "baja", "resolved", 60, 40),              # met (40<=48)
    ("La app no guarda cambios offline", "App Móvil", "media", "open", 23, None),               # due_soon
    ("Solicito alta de nuevo usuario", "General", "baja", "open", 5, None),                     # on_track
    ("Pago rechazado sin motivo claro", "Facturación", "urgente", "in_progress", 1, None),      # on_track
]


def main():
    db.ensure_schema()
    conn = db.get_conn()

    for name in CATEGORIES:
        conn.run("INSERT INTO categories (name) VALUES (:n) ON CONFLICT (name) DO NOTHING", n=name)
    cat_id = {r["name"]: r["id"] for r in db.query("SELECT id, name FROM categories")}

    for cat, subs in SUBCATEGORIES.items():
        for s in subs:
            if not db.query_one("SELECT 1 AS ok FROM subcategories WHERE name=:s AND category_id=:c", s=s, c=cat_id[cat]):
                conn.run("INSERT INTO subcategories (name, category_id) VALUES (:s, :c)", s=s, c=cat_id[cat])

    from app import auth
    agent_ids = []
    for email, nm in AGENTS:
        row = db.query_one("SELECT id FROM users WHERE email=:e", e=email)
        if not row:
            salt, h = auth.hash_password("agente123")
            row = db.execute(
                "INSERT INTO users (email, name, role, password_hash, password_salt) VALUES (:e,:n,'agent',:h,:s) RETURNING id",
                e=email, n=nm, h=h, s=salt)[0]
        agent_ids.append(row["id"])

    admin = db.query_one("SELECT id FROM users WHERE role='admin' ORDER BY id LIMIT 1")
    requester_id = admin["id"]
    pri_id = {r["name"]: r["id"] for r in db.query("SELECT id, name FROM priorities")}

    created = 0
    for i, (subject, cat, pri, status, age_h, res_after) in enumerate(TICKETS):
        assignee = agent_ids[i % len(agent_ids)] if status != "open" else (agent_ids[i % len(agent_ids)] if i % 2 else None)
        resolved_clause = "NULL"
        params = {
            "s": subject, "d": f"Ticket de demostración: {subject}.",
            "c": cat_id[cat], "p": pri_id[pri], "st": status,
            "r": requester_id, "a": assignee, "age": age_h,
        }
        if res_after is not None:
            resolved_clause = "now() - make_interval(hours => :age) + make_interval(hours => :res)"
            params["res"] = res_after
        row = conn.run(
            f"""INSERT INTO tickets (subject, description, category_id, priority_id, status, requester_id,
                       assignee_id, created_at, updated_at, resolved_at)
                VALUES (:s, :d, :c, :p, :st, :r, :a,
                        now() - make_interval(hours => :age),
                        now() - make_interval(hours => :age),
                        {resolved_clause})
                RETURNING id""", **params)
        tid = row[0][0]
        # un comentario en algunos
        if i % 3 == 0:
            conn.run("INSERT INTO ticket_comments (ticket_id, author_id, body) VALUES (:t,:a,:b)",
                     t=tid, a=assignee or requester_id, b="Revisando el caso, te actualizo pronto.")
        created += 1

    total = db.query_one("SELECT count(*) AS n FROM tickets")["n"]
    print(f"Insertados {created} tickets dummy. Total en BD: {total}")
    dist = db.query("""SELECT sla_status, count(*) AS n FROM (
        SELECT CASE
          WHEN t.status IN ('resolved','closed') THEN
            CASE WHEN t.resolved_at <= t.created_at + make_interval(hours => p.sla_hours) THEN 'met' ELSE 'breached' END
          WHEN now() > t.created_at + make_interval(hours => p.sla_hours) THEN 'breached'
          WHEN now() > t.created_at + make_interval(mins => p.sla_hours*48) THEN 'due_soon'
          ELSE 'on_track' END AS sla_status
        FROM tickets t JOIN priorities p ON p.id = t.priority_id) x
        GROUP BY sla_status ORDER BY sla_status""")
    print("Distribución SLA:", {r["sla_status"]: r["n"] for r in dist})


if __name__ == "__main__":
    main()
