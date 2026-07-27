"""JWT access / refresh tokens (HS256). Compatible avec X-API-Token existant."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

JWT_SECRET = os.getenv("JWT_SECRET", "kalitao-test-secret-change-me-32b!")
JWT_ALGORITHM = "HS256"
ACCESS_TTL_MINUTES = int(os.getenv("JWT_ACCESS_TTL_MINUTES", "60"))
REFRESH_TTL_DAYS = int(os.getenv("JWT_REFRESH_TTL_DAYS", "30"))


def create_access_token(utilisateur_id: str, *, extra: dict[str, Any] | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": utilisateur_id,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TTL_MINUTES),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(utilisateur_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": utilisateur_id,
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=REFRESH_TTL_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str, *, expected_type: str | None = None) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise ValueError("Token JWT invalide ou expiré") from exc
    if expected_type and payload.get("type") != expected_type:
        raise ValueError(f"Token de type {expected_type} attendu")
    if not payload.get("sub"):
        raise ValueError("Token JWT sans sujet")
    return payload
