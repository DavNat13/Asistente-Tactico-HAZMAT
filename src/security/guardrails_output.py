"""Guardrails de SALIDA:

- Elimina HTML / URLs javascript: (OWASP LLM05 — manejo inseguro de la salida → XSS).
- Detecta y redacta secretos (API keys, cadenas de conexión) y fuga del prompt de sistema.
- Grounding: proporción de páginas citadas que existen en los documentos recuperados.
"""

from __future__ import annotations

import re

from src.security.text import strip_markup

_HTML_TAG = re.compile(r"<\s*/?\s*[a-zA-Z][^>]*>")
_JS_URL = re.compile(r"javascript\s*:", re.IGNORECASE)
_LEAKS = [
    re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),
    re.compile(r"mongodb(\+srv)?://\S+", re.IGNORECASE),
    re.compile(r"(?i)(GEMINI_API_KEYS|MONGODB_URI|LANGCHAIN_API_KEY)\s*="),
]
PROMPT_FINGERPRINTS = ("REGLAS DE OPERACIÓN", "<documentos>", "FORMATO DE RESPUESTA")
_PAGE_CITE = re.compile(r"\bp(?:á|a)?g?(?:ina)?s?\.?\s*(\d{1,3})\b", re.IGNORECASE)


def sanitize_output(text: str) -> tuple[str, list[str]]:
    """Devuelve (texto_seguro, problemas_detectados)."""
    text = text or ""
    issues = []
    if _HTML_TAG.search(text):
        issues.append("html")
        text = strip_markup(text)
    if _JS_URL.search(text):
        issues.append("js_url")
        text = _JS_URL.sub("", text)
    for p in _LEAKS:
        if p.search(text):
            issues.append("secret")
            text = p.sub("[REDACTADO]", text)
    if any(fp in text for fp in PROMPT_FINGERPRINTS):
        issues.append("prompt_leak")
    return text, issues


def cited_pages(text: str) -> set[str]:
    return set(_PAGE_CITE.findall(text or ""))


def grounding(answer: str, docs: list[dict]) -> dict:
    cited = cited_pages(answer)
    available: set[str] = set()
    for d in docs:
        md = d.get("metadata", {})
        available.update(
            str(v)
            for v in (md.get("page_label"), md.get("page_number"))
            if v is not None
        )
    if not cited:
        return {"citations": 0, "grounded": None, "unsupported": []}
    unsupported = sorted(cited - available)
    return {
        "citations": len(cited),
        "grounded": round(1 - len(unsupported) / len(cited), 3),
        "unsupported": unsupported,
    }
