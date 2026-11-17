"""Índice estructurado de N° UN a partir de las páginas amarillas y la Tabla 1 de la GRE 2024.

Permite búsquedas EXACTAS (UN → guía, nombres, fila de Tabla 1) que la búsqueda vectorial no resuelve bien.
"""

from __future__ import annotations

import re

from langchain_core.documents import Document

from src.ingesta.processor import normalize

_YELLOW_ROW = re.compile(r"^(\d{4}) (\d{3}P?) (.+)$")
_T1_ROW = re.compile(r"^(\d{4}) (\d{3}P?) (.+)$")
_HEADER_WORDS = ("Nro.", "ID", "Guía", "Nombre del Material", "GRE2024")


def _is_header(line: str) -> bool:
    return (
        not line
        or any(line.startswith(w) for w in _HEADER_WORDS)
        or line.startswith("Página")
    )


def build_un_index(documents: list[Document]) -> list[dict]:
    """Parsea páginas amarillas (UN → guía → nombres) y filas de la Tabla 1."""
    entries: dict[str, dict] = {}
    for doc in documents:
        meta = doc.metadata
        if meta.get("section") != "amarillas":
            continue
        lines = [ln.strip() for ln in doc.page_content.split("\n")]
        current = None
        for ln in lines:
            m = _YELLOW_ROW.match(ln)
            if m:
                un, guide, name = m.groups()
                e = entries.setdefault(
                    un, {"un": un, "guides": [], "names": [], "pages": []}
                )
                if guide not in e["guides"]:
                    e["guides"].append(guide)
                e["names"].append(name.strip())
                if meta["page_label"] not in e["pages"]:
                    e["pages"].append(meta["page_label"])
                current = e
            elif current and not _is_header(ln) and not re.match(r"^\d", ln):
                current["names"][-1] = f"{current['names'][-1]} {ln}".strip()
            else:
                current = None

    for doc in documents:
        meta = doc.metadata
        if meta.get("section") != "tabla1":
            continue
        lines = [ln.strip() for ln in doc.page_content.split("\n")]
        for idx, ln in enumerate(lines):
            m = _T1_ROW.match(ln)
            if not m or m.group(1) not in entries:
                continue
            row = ln
            if " m (" not in row and idx + 1 < len(
                lines
            ):  # distancias en la línea siguiente
                row = f"{row} {lines[idx + 1]}"
            e = entries[m.group(1)]
            e.setdefault("tabla1", [])
            if len(e["tabla1"]) < 4:
                e["tabla1"].append({"row": row, "page_label": meta["page_label"]})

    out = []
    for e in entries.values():
        e["names"] = list(dict.fromkeys(e["names"]))
        e["names_norm"] = [normalize(n) for n in e["names"]]
        e["in_tabla1"] = bool(e.get("tabla1"))
        e["_id"] = e["un"]
        out.append(e)
    print(f"Índice UN: {len(out)} números UN")
    return out
