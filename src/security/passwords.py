"""Contraseñas: scrypt (resistente a fuerza bruta por GPU, stdlib) + sal única + comparación constante."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os

MIN_PASSWORD = 10
_N, _R, _P = 2**14, 8, 1


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=64)
    b64 = base64.b64encode
    return f"scrypt${_N}${_R}${_P}${b64(salt).decode()}${b64(dk).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, n, r, p, salt, digest = stored.split("$")
        if algo != "scrypt":
            return False
        dk = hashlib.scrypt(
            password.encode(),
            salt=base64.b64decode(salt),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=64,
        )
        return hmac.compare_digest(dk, base64.b64decode(digest))
    except (ValueError, TypeError):
        return False


def validate_password(password: str) -> None:
    if len(password) < MIN_PASSWORD:
        raise ValueError(f"La contraseña debe tener al menos {MIN_PASSWORD} caracteres")
    if password.isalpha() or password.isdigit():
        raise ValueError("La contraseña debe combinar letras y números o símbolos")
    if password.strip() != password:
        raise ValueError("La contraseña no puede empezar ni terminar con espacios")
