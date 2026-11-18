"""Redacción de datos personales (Ley 19.628 / Ley 21.719 de Protección de Datos Personales, Chile).

Se aplica ANTES de enviar texto al LLM (proveedor externo) y ANTES de persistir historial o logs.
Principio de minimización: el asistente no necesita datos personales para responder sobre HAZMAT.
"""

from __future__ import annotations

import re

# Orden importa: patrones más específicos primero.
_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    ("RUT", re.compile(r"\b\d{1,2}\.?\d{3}\.?\d{3}-?[\dkK]\b")),
    ("TELEFONO", re.compile(r"(?:\+?56\s?)?(?:\(?0?9\)?\s?)\d{4}\s?\d{4}\b")),
    ("TELEFONO", re.compile(r"\+?56\s?\d{1,2}\s?\d{3,4}\s?\d{4}\b")),
    ("TARJETA", re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b")),
    # Patente chilena: LLLL-NN / LL-NNNN. Se excluyen "UN 1203", "ID 1203", "NU 1203" (N° ONU).
    (
        "PATENTE",
        re.compile(r"\b[A-Z]{4}[- ]\d{2}\b|\b(?!(?:UN|ID|NU)[- ])[A-Z]{2}[- ]\d{4}\b"),
    ),
]


def redact(text: str) -> tuple[str, int]:
    """Devuelve (texto_redactado, cantidad_de_reemplazos)."""
    if not text:
        return text, 0
    total = 0
    for label, pattern in _PATTERNS:
        text, n = pattern.subn(f"[{label}]", text)
        total += n
    return text, total


def contains_pii(text: str) -> bool:
    return redact(text)[1] > 0
