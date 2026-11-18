"""Limpieza de texto para MOSTRAR y GUARDAR: el chat nunca muestra código HTML/JS.

Se elimina el contenido completo de bloques ejecutables (<script>, <style>, <iframe>…), luego
cualquier etiqueta HTML restante, URLs `javascript:` y manejadores `on*=`. El resultado es texto
plano que se renderiza como markdown sin HTML.
"""

from __future__ import annotations

import html
import re

_BLOCKS = re.compile(
    r"<\s*(script|style|iframe|object|embed|svg|template|noscript)\b[^>]*>.*?<\s*/\s*\1\s*>",
    re.IGNORECASE | re.DOTALL,
)
_OPEN_BLOCK = re.compile(
    r"<\s*(script|style|iframe|object|embed|svg)\b[^>]*>.*\Z", re.IGNORECASE | re.DOTALL
)
_TAGS = re.compile(r"<\s*/?\s*[a-zA-Z!][^>]*>")
_JS = re.compile(r"javascript\s*:", re.IGNORECASE)
_HANDLERS = re.compile(r"\bon[a-z]+\s*=\s*(['\"]).*?\1", re.IGNORECASE)
_SPACES = re.compile(r"[ \t]{2,}")


def strip_markup(text: str) -> str:
    """Devuelve el texto sin ningún fragmento de HTML/JS ejecutable."""
    if not text:
        return ""
    t = html.unescape(text)  # &lt;script&gt; también cuenta como código
    t = _BLOCKS.sub(" ", t)
    t = _OPEN_BLOCK.sub(" ", t)
    t = _TAGS.sub(" ", t)
    t = _JS.sub("", t)
    t = _HANDLERS.sub("", t)
    t = t.replace("<", "‹").replace(">", "›")  # restos sueltos: inofensivos y visibles
    return "\n".join(_SPACES.sub(" ", ln).strip() for ln in t.splitlines()).strip()


def had_markup(original: str, cleaned: str) -> bool:
    return (
        bool(_TAGS.search(html.unescape(original or "")))
        and original.strip() != cleaned
    )
