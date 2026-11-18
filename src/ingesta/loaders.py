"""Carga de PDFs con metadatos estructurales de la GRE 2024.

Cada página se etiqueta con:
- source       : nombre legible del documento ("GRE 2024" / "Manual ABC-V")
- file         : nombre del archivo
- page         : página física del PDF (1-based)
- page_label   : página IMPRESA (la que ve el bombero en el libro)
- section      : amarillas | azules | guia | tabla1 | tabla2 | tabla3 | general
- guide_number : número de guía naranja (solo section == "guia")
- guide_title  : título de la guía
"""

from __future__ import annotations

import os
import re

from langchain_core.documents import Document
from pypdf import PdfReader

DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data"
)

SOURCE_NAMES = {
    "gre_2024.pdf": "GRE 2024",
    "manual-abc-v.pdf": "Manual ABC-V",
}

_FOOTER_PAGE = re.compile(r"P[áa]gina\s+(\d{1,3})\s*$")
_GUIDE_FOOTER = re.compile(
    r"GU[ÍI]A\s*\n\s*(\d{3})\s*\n(.+?)\n\s*P[áa]gina\s+\d+\s*$", re.DOTALL
)
_YELLOW_LINE = re.compile(r"(?m)^\d{4} \d{3}P? \S")
_BLUE_LINE = re.compile(r"(?m)\S \d{3}P? \d{4}\s*$")


def source_name(path: str) -> str:
    base = os.path.basename(path)
    return SOURCE_NAMES.get(base.lower(), os.path.splitext(base)[0])


def classify_page(text: str) -> dict:
    """Detecta la sección de la GRE a la que pertenece una página."""
    head = text[:400].upper()
    m = _GUIDE_FOOTER.search(text[-200:])
    if m:
        title = re.sub(r"\s+", " ", m.group(2)).strip()
        return {"section": "guia", "guide_number": m.group(1), "guide_title": title}
    for n in ("1", "2", "3"):
        if f"TABLA {n} -" in head or f"TABLA {n}–" in head or f"TABLA {n} —" in head:
            return {"section": f"tabla{n}"}
    if len(_YELLOW_LINE.findall(text)) >= 8:
        return {"section": "amarillas"}
    if len(_BLUE_LINE.findall(text)) >= 8:
        return {"section": "azules"}
    return {"section": "general"}


def load_single_pdf(pdf_path: str) -> list[Document]:
    reader = PdfReader(pdf_path)
    try:
        labels = reader.page_labels
    except Exception:  # noqa: BLE001 — PDFs sin etiquetas
        labels = []
    src, fname = source_name(pdf_path), os.path.basename(pdf_path)
    docs = []
    for i, page in enumerate(reader.pages):
        text = (page.extract_text() or "").strip()
        if not text:
            continue
        label = None
        m = _FOOTER_PAGE.search(text[-40:])
        if m:
            label = m.group(1)
        elif labels and i < len(labels):
            label = labels[i]
        meta = {
            "source": src,
            "file": fname,
            "page": i + 1,
            "page_label": str(label or i + 1),
        }
        if src == "GRE 2024":
            meta.update(classify_page(text))
        else:
            meta["section"] = "general"
        docs.append(Document(page_content=text, metadata=meta))
    print(f"{fname}: {len(docs)} páginas con texto")
    return docs


def load_directory(directory: str | None = None) -> list[Document]:
    directory = directory or DATA_DIR
    if not os.path.isdir(directory):
        print(f"Directorio no encontrado: {directory}")
        return []
    docs: list[Document] = []
    for name in sorted(os.listdir(directory)):
        if name.lower().endswith(".pdf"):
            docs.extend(load_single_pdf(os.path.join(directory, name)))
    return docs
