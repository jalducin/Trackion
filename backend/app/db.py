"""Capa de datos: conexión PostgreSQL (pg8000), helpers parametrizados y esquema idempotente."""
import ssl

from pg8000.native import Connection, DatabaseError

from . import config

_conn = None


def _ssl_context():
    if not config.DB_SSL:
        return None
    # develop: TLS sin verificación de CA (RDS). En prod, verificar contra el CA bundle de RDS.
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _connect() -> Connection:
    return Connection(
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        host=config.DB_HOST,
        port=config.DB_PORT,
        database=config.DB_NAME,
        ssl_context=_ssl_context(),
        timeout=10,
    )


def get_conn() -> Connection:
    """Devuelve una conexión viva, reusándola entre invocaciones cálidas del Lambda."""
    global _conn
    if _conn is None:
        _conn = _connect()
        return _conn
    try:
        _conn.run("SELECT 1")
    except Exception:
        try:
            _conn.close()
        except Exception:
            pass
        _conn = _connect()
    return _conn


def query(sql: str, **params) -> list:
    """Ejecuta una consulta parametrizada (`:nombre`) y devuelve filas como dicts."""
    conn = get_conn()
    rows = conn.run(sql, **params)
    cols = [c["name"] for c in conn.columns] if conn.columns else []
    return [dict(zip(cols, row)) for row in rows]


def query_one(sql: str, **params):
    rows = query(sql, **params)
    return rows[0] if rows else None


def execute(sql: str, **params) -> list:
    """Ejecuta una sentencia (INSERT/UPDATE/DELETE). Devuelve filas si hay RETURNING."""
    conn = get_conn()
    rows = conn.run(sql, **params)
    if conn.columns:
        cols = [c["name"] for c in conn.columns]
        return [dict(zip(cols, row)) for row in rows]
    return []


def db_up() -> bool:
    try:
        get_conn().run("SELECT 1")
        return True
    except Exception:
        return False


SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id            SERIAL PRIMARY KEY,
        email         TEXT UNIQUE NOT NULL,
        name          TEXT NOT NULL,
        role          TEXT NOT NULL DEFAULT 'agent',
        password_hash TEXT NOT NULL,
        password_salt TEXT NOT NULL,
        is_active     BOOLEAN NOT NULL DEFAULT TRUE,
        created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS categories (
        id         SERIAL PRIMARY KEY,
        name       TEXT UNIQUE NOT NULL,
        is_active  BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS subcategories (
        id          SERIAL PRIMARY KEY,
        category_id INTEGER NOT NULL REFERENCES categories(id),
        name        TEXT NOT NULL,
        is_active   BOOLEAN NOT NULL DEFAULT TRUE,
        created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS priorities (
        id        SERIAL PRIMARY KEY,
        name      TEXT UNIQUE NOT NULL,
        level     INTEGER NOT NULL DEFAULT 0,
        is_active BOOLEAN NOT NULL DEFAULT TRUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tickets (
        id             SERIAL PRIMARY KEY,
        subject        TEXT NOT NULL,
        description    TEXT NOT NULL DEFAULT '',
        category_id    INTEGER NOT NULL REFERENCES categories(id),
        subcategory_id INTEGER REFERENCES subcategories(id),
        priority_id    INTEGER NOT NULL REFERENCES priorities(id),
        status         TEXT NOT NULL DEFAULT 'open',
        requester_id   INTEGER NOT NULL REFERENCES users(id),
        assignee_id    INTEGER REFERENCES users(id),
        created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
        resolved_at    TIMESTAMPTZ
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ticket_comments (
        id         SERIAL PRIMARY KEY,
        ticket_id  INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
        author_id  INTEGER NOT NULL REFERENCES users(id),
        body       TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS integrations (
        id         SERIAL PRIMARY KEY,
        name       TEXT UNIQUE NOT NULL,
        is_active  BOOLEAN NOT NULL DEFAULT FALSE,
        config     JSONB NOT NULL DEFAULT '{}'::jsonb,
        events     TEXT[] NOT NULL DEFAULT '{}',
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS integrations_log (
        id               SERIAL PRIMARY KEY,
        integration_name TEXT NOT NULL,
        event            TEXT NOT NULL,
        status           TEXT NOT NULL,
        detail           TEXT,
        created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status)",
    "CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON tickets(created_at)",
    "CREATE INDEX IF NOT EXISTS idx_tickets_assignee ON tickets(assignee_id)",
]


def ensure_schema():
    """Crea las tablas (idempotente) y siembra datos base."""
    conn = get_conn()
    for stmt in SCHEMA_STATEMENTS:
        conn.run(stmt)
    _seed(conn)


def _seed(conn: Connection):
    from . import auth  # import diferido para evitar ciclo

    # Prioridades base
    for name, level in [("baja", 1), ("media", 2), ("alta", 3), ("urgente", 4)]:
        conn.run(
            "INSERT INTO priorities (name, level) VALUES (:n, :l) ON CONFLICT (name) DO NOTHING",
            n=name, l=level,
        )
    # Categoría general
    conn.run(
        "INSERT INTO categories (name) VALUES ('General') ON CONFLICT (name) DO NOTHING"
    )
    # Usuario admin semilla
    existing = conn.run("SELECT id FROM users WHERE email = :e", e=config.ADMIN_EMAIL)
    if not existing:
        salt, pwd_hash = auth.hash_password(config.ADMIN_PASSWORD)
        conn.run(
            """INSERT INTO users (email, name, role, password_hash, password_salt)
               VALUES (:e, :n, 'admin', :h, :s)""",
            e=config.ADMIN_EMAIL, n="Administrador", h=pwd_hash, s=salt,
        )
