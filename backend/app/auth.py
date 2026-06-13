"""Autenticación: hash de contraseñas (PBKDF2), emisión/validación de JWT y handlers."""
import hashlib
import hmac
import os
import time

import jwt

from . import config, db
from .http import ApiError, build_response, parse_body, require_field

_PBKDF2_ITERATIONS = 200_000
_PBKDF2_ALGO = "sha256"


def hash_password(password: str):
    """Devuelve (salt_hex, hash_hex) usando PBKDF2-HMAC-SHA256."""
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(_PBKDF2_ALGO, password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
    return salt.hex(), digest.hex()


def verify_password(password: str, salt_hex: str, hash_hex: str) -> bool:
    salt = bytes.fromhex(salt_hex)
    digest = hashlib.pbkdf2_hmac(_PBKDF2_ALGO, password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
    return hmac.compare_digest(digest.hex(), hash_hex)


def make_token(user: dict) -> str:
    now = int(time.time())
    payload = {
        "sub": str(user["id"]),
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "iat": now,
        "exp": now + config.JWT_TTL_SECONDS,
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, config.JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise ApiError(401, "token_expired", "El token expiró")
    except jwt.InvalidTokenError:
        raise ApiError(401, "token_invalid", "Token inválido")


def bearer_from_header(authorization: str):
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


# ── Handlers ──

def login(event):
    data = parse_body(event)
    email = require_field(data, "email")
    password = require_field(data, "password")
    user = db.query_one(
        "SELECT id, email, name, role, password_hash, password_salt, is_active FROM users WHERE email = :e",
        e=email,
    )
    if not user or not verify_password(password, user["password_salt"], user["password_hash"]):
        raise ApiError(401, "invalid_credentials", "Credenciales inválidas")
    if not user["is_active"]:
        raise ApiError(403, "user_inactive", "El usuario está inactivo")
    token = make_token(user)
    return build_response(200, {
        "token": token,
        "user": {"id": user["id"], "email": user["email"], "name": user["name"], "role": user["role"]},
    })


def me(event):
    ident = (event.get("requestContext") or {}).get("authorizer", {}).get("lambda", {})
    return build_response(200, {
        "id": ident.get("sub"),
        "email": ident.get("email"),
        "name": ident.get("name"),
        "role": ident.get("role"),
    })
