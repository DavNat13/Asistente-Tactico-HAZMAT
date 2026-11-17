"""Prefetch determinista de contexto: resuelve material → N° UN → guía ANTES de llamar al LLM.

Ahorra llamadas de herramientas (menos latencia y tokens) y evita que la búsqueda semántica
confunda guías de redacción similar.
"""

from __future__ import annotations

import logging

from src.agent.router import Route
from src.ingesta.processor import normalize
from src.retrieval.retriever import retriever

log = logging.getLogger("hazmat.context")

_STOP_WORDS = (
    "que cual cuales guia numero uso usar para del las los una por con como segun debo hago tabla "
    "distancia distancias aislamiento aislar inicial evacuacion evacuar derrame derrames fuga fugas "
    "incendio grande pequeno pequena agente agentes extintor extingo minimo minima favor viento "
    "corresponde aplica liquido solido gas camion cisterna autotanque ruta respondo accion acciones "
    "equipo proteccion necesito plan respuesta pasos inmediatos identificacion contengo contener "
    "laboratorio bodega planta involucrado expuesto fuego patio residencial cerca viviendas "
    "carretera nube visible noche esta sobre entre donde cuanto cuantos hacer debe deben tiene puede "
)
_STOP = frozenset(_STOP_WORDS.split())


def un_entry_docs(entry: dict) -> list[dict]:
    """Convierte una entrada del índice UN en documentos citables."""
    names = "; ".join(entry.get("names", [])[:4])
    guides = ", ".join(entry.get("guides", []))
    page = (entry.get("pages") or ["?"])[0]
    t1 = (
        "Sí (material resaltado: consultar Tabla 1)" if entry.get("in_tabla1") else "No"
    )
    docs = [
        {
            "_id": f"un-{entry['un']}",
            "text": f"GRE 2024 · Páginas amarillas · Página {page}\nUN {entry['un']} → Guía {guides} · "
            f"Nombres: {names} · En Tabla 1: {t1}\n"
            # fila literal tal como aparece en el libro (N° ID · Guía · Material)
            f"{entry['un']} {guides.split(',')[0]} {entry.get('names', [''])[0]}",
            "metadata": {
                "source": "GRE 2024",
                "page_label": page,
                "section": "amarillas",
            },
            "score": 1.0,
            "match": "exacto",
        }
    ]
    for row in entry.get("tabla1", [])[:2]:
        docs.append(
            {
                "_id": f"t1-{entry['un']}-{row['page_label']}",
                "text": f"GRE 2024 · Tabla 1 — Distancias de aislamiento inicial y acción protectora · "
                f"Página {row['page_label']}\nColumnas: N° UN | Guía | Material | DERRAME PEQUEÑO: "
                f"aislar a la redonda | proteger día | proteger noche | DERRAME GRANDE: aislar | "
                f"proteger día | proteger noche\n{row['row']}",
                "metadata": {
                    "source": "GRE 2024",
                    "page_label": row["page_label"],
                    "section": "tabla1",
                },
                "score": 1.0,
                "match": "exacto",
            }
        )
    return docs


def find_materials(query: str, limit: int = 2) -> list[dict]:
    """Extrae nombres de material de la consulta probando frases → bigramas → palabras."""
    words = [
        w
        for w in normalize(query).split()
        if len(w) > 2 and w not in _STOP and not w.isdigit()
    ]
    candidates = [" ".join(words[i : i + 2]) for i in range(len(words) - 1)] + [
        w for w in words if len(w) >= 4
    ]
    found: dict[str, dict] = {}
    used: set[str] = set()
    for cand in candidates:
        if used & set(cand.split()):  # palabra ya consumida por un material encontrado
            continue
        hits = retriever.search_material(cand, limit=3)
        exact = [h for h in hits if normalize(h["names"][0]).startswith(cand)]
        for h in (exact or hits)[:1]:
            found.setdefault(h["un"], h)
            used.update(cand.split())
        if len(found) >= limit:
            break
    return list(found.values())


def prefetch(route: Route, query: str) -> list[dict]:
    docs: list[dict] = []
    guides: list[str] = list(route.guides)
    entries = [e for e in (retriever.lookup_un(un) for un in route.un_numbers) if e]
    if not entries and not guides:
        entries = find_materials(query)
    for e in entries:
        docs.extend(un_entry_docs(e))
        guides.extend(g.rstrip("P") for g in e.get("guides", [])[:1])
    for g in list(dict.fromkeys(guides))[:2]:
        docs.extend(retriever.get_guide(g))
    k = 4 if route.complexity == "medium" else 6
    docs.extend(retriever.hybrid_search(query, k))
    unique = list({d["_id"]: d for d in docs}.values())
    log.info(
        "prefetch un=%s guides=%s docs=%d",
        [e["un"] for e in entries],
        guides,
        len(unique),
    )
    return unique


def format_docs(docs: list[dict], max_chars: int = 18000) -> str:
    parts, total = [], 0
    for d in docs:
        text = d.get("text", "").strip()
        if total + len(text) > max_chars:
            break
        parts.append(text)
        total += len(text)
    return "\n\n---\n\n".join(parts) or "(sin documentos)"
