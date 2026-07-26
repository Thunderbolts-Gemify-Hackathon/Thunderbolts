"""Hachage de mot de passe (PBKDF2-HMAC, sans dépendance externe)."""

from __future__ import annotations

import hashlib
import hmac
import secrets

_ALGO = "sha256"
_ITERATIONS = 200_000


def hash_password(mot_de_passe: str) -> str:
    sel = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(_ALGO, mot_de_passe.encode("utf-8"), sel.encode("utf-8"), _ITERATIONS)
    return f"{sel}${digest.hex()}"


def verify_password(mot_de_passe: str, hash_stocke: str) -> bool:
    if not hash_stocke or "$" not in hash_stocke:
        return False
    sel, digest_hex = hash_stocke.split("$", 1)
    digest = hashlib.pbkdf2_hmac(_ALGO, mot_de_passe.encode("utf-8"), sel.encode("utf-8"), _ITERATIONS)
    return hmac.compare_digest(digest.hex(), digest_hex)
