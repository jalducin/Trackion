"""Pruebas de autenticación: hash PBKDF2 y JWT."""
import time

import jwt
import pytest

from app import auth, config
from app.http import ApiError


def test_hash_password_roundtrip():
    salt, h = auth.hash_password("secreto123")
    assert salt and h
    assert auth.verify_password("secreto123", salt, h) is True


def test_hash_password_rejects_wrong():
    salt, h = auth.hash_password("secreto123")
    assert auth.verify_password("otra", salt, h) is False


def test_hash_uses_random_salt():
    s1, h1 = auth.hash_password("misma")
    s2, h2 = auth.hash_password("misma")
    assert s1 != s2 and h1 != h2  # salt aleatorio → hashes distintos


def test_token_roundtrip():
    token = auth.make_token({"id": 7, "email": "a@b.c", "name": "Ana", "role": "agent"})
    claims = auth.decode_token(token)
    assert claims["sub"] == "7"
    assert claims["email"] == "a@b.c"
    assert claims["role"] == "agent"


def test_token_expired():
    now = int(time.time())
    token = jwt.encode(
        {"sub": "1", "iat": now - 100, "exp": now - 10}, config.JWT_SECRET, algorithm="HS256"
    )
    with pytest.raises(ApiError) as exc:
        auth.decode_token(token)
    assert exc.value.status == 401


def test_token_bad_signature():
    token = jwt.encode({"sub": "1"}, "otro-secreto", algorithm="HS256")
    with pytest.raises(ApiError):
        auth.decode_token(token)


def test_bearer_parsing():
    assert auth.bearer_from_header("Bearer abc.def.ghi") == "abc.def.ghi"
    assert auth.bearer_from_header("Token abc") is None
    assert auth.bearer_from_header("") is None
