"""Herramientas del agente HAZMAT. Devuelven (texto para el LLM, documentos como artefacto)."""

from __future__ import annotations

import re
import time
from typing import Literal

from langchain_core.tools import tool

from src.agent.context import format_docs, un_entry_docs
from src.observability.telemetry import current
from src.retrieval.retriever import retriever


def _timed(name: str, fn):
    t0 = time.perf_counter()
    docs = fn()
    rec = current()
    if rec is not None:
        rec.tool(name, (time.perf_counter() - t0) * 1000, len(docs))
    return docs


@tool(response_format="content_and_artifact")
def buscar_material(consulta: str) -> tuple[str, list]:
    """Identifica un material peligroso por N° UN (4 dígitos) o por nombre.
    Devuelve N° UN, guía naranja, nombres oficiales y, si corresponde, la fila de la Tabla 1
    (distancias de aislamiento inicial y acción protectora)."""

    def run():
        uns = re.findall(r"\b(\d{4})\b", consulta)
        entries = [e for e in (retriever.lookup_un(u) for u in uns[:3]) if e]
        if not entries:
            entries = retriever.search_material(consulta, limit=4)
        return [d for e in entries for d in un_entry_docs(e)]

    docs = _timed("buscar_material", run)
    return (
        format_docs(docs)
        if docs
        else "Sin coincidencias para ese N° UN o nombre en la GRE 2024."
    ), docs


@tool(response_format="content_and_artifact")
def obtener_guia(numero_guia: str) -> tuple[str, list]:
    """Devuelve el texto completo de una guía naranja de la GRE 2024 (111-174): peligros potenciales,
    seguridad pública, ropa protectora, evacuación, fuego, derrame o fuga y primeros auxilios."""
    docs = _timed("obtener_guia", lambda: retriever.get_guide(numero_guia))
    return (
        format_docs(docs)
        if docs
        else f"La guía {numero_guia} no existe o no tiene contenido."
    ), docs


@tool(response_format="content_and_artifact")
def buscar_manual(
    consulta: str, fuente: Literal["GRE 2024", "Manual ABC-V", "todas"] = "todas"
) -> tuple[str, list]:
    """Búsqueda semántica y por palabras clave en la GRE 2024 y el Manual ABC-V. Úsala para temas
    generales (zonas de trabajo, descontaminación, clases de riesgo, procedimientos ABC-V)."""
    source = None if fuente == "todas" else fuente
    docs = _timed("buscar_manual", lambda: retriever.hybrid_search(consulta, 5, source))
    return (
        format_docs(docs)
        if docs
        else "Sin resultados en los manuales para esta búsqueda."
    ), docs


TOOLS = [buscar_material, obtener_guia, buscar_manual]
