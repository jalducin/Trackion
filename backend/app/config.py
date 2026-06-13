"""Configuración leída de variables de entorno (inyectadas desde SSM por serverless.yml)."""
import os


def _bool(value: str) -> bool:
    return str(value).strip().lower() in ("1", "true", "yes", "on")


STAGE = os.environ.get("STAGE", "develop")
APP_VERSION = os.environ.get("APP_VERSION", "0.0.0")

# Base de datos PostgreSQL (RDS)
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))
DB_NAME = os.environ.get("DB_NAME", "trackion")
DB_USER = os.environ.get("DB_USER", "trackion")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_SSL = _bool(os.environ.get("DB_SSL", "true"))

# Autenticación
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-insecure-change-me")
JWT_TTL_SECONDS = int(os.environ.get("JWT_TTL_SECONDS", "28800"))

# Usuario administrador semilla (creado en ensure_schema si no existe)
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@trackion.local")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "changeme")
