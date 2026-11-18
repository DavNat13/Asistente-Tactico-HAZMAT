"""Clasificador de complejidad de la consulta (sin LLM, determinista y auditable).

- low    : saludo, agradecimiento, identidad/capacidades del asistente → respuesta directa, 0 tokens.
- medium : dato puntual (N° UN, guía, distancia, agente extintor, EPP) → RAG + 1-2 llamadas LLM.
- high   : escenario de incidente multi-paso → agente con más herramientas y plantilla de plan.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from src.security.patterns import norm

_GREET = r"(hola|holi|hey|buenas|buenos dias|buenas tardes|buenas noches|saludos)"
_THANKS = r"(gracias|muchas gracias|te pasaste|excelente|perfecto|ok|vale|genial)"
_ID = r"(quien eres|que eres|como te llamas|presentate|hablame de ti|cuentame de ti)"
_CAP = (
    r"(que puedes hacer|que haces|para que sirves|en que me puedes ayudar|como puedes ayudarme|"
    r"que sabes hacer|cuales son tus capacidades|ayuda)"
)
_LOW_PATTERNS = [
    re.compile(rf"^{_GREET}( {_ID}| {_CAP})?$"),
    re.compile(rf"^({_GREET} )?{_ID}$"),
    re.compile(rf"^({_GREET} )?{_CAP}$"),
    re.compile(rf"^{_THANKS}( \w+){{0,4}}$"),
]
_THANKS_RE = re.compile(rf"^{_THANKS}\b")

_UN_RE = re.compile(r"\b(?:un|onu|id|n[°º]?)?\s?(\d{4})\b")
_GUIDE_RE = re.compile(r"\bguia\s*(?:n[°º]?|numero|nro)?\s*(1[1-7]\d)\b")
_SCENARIO = re.compile(
    r"\b(volcad\w*|accidente|colision|choque|cisterna|camion|vagon|bodega|planta|laboratorio|patio|"
    r"residencial|domicilio|casa|edificio|viviendas?|colegio|ruta|carretera|tunel|nube|victimas?|heridos?|"
    r"lesionados?|plan|como respondo|que hago|que debo hacer|pasos|zona caliente|incidente)\b"
)
_ASPECTS = re.compile(
    r"\b(identificacion|aislamiento|aislar|evacuacion|evacuar|acciones|epp|epi|equipo de proteccion|"
    r"primeros auxilios|conten\w+|tacticas?|distancias|descontaminacion)\b"
)
_EVENT = re.compile(
    r"\b(derrame|fuga|escape|incendio|explosion|emanacion|filtracion|expuesto al fuego)\b"
)


@dataclass
class Route:
    complexity: str  # low | medium | high
    intent: str = "consulta"  # saludo | gracias | consulta | incidente
    un_numbers: list[str] = field(default_factory=list)
    guides: list[str] = field(default_factory=list)
    reason: str = ""


def _valid_un(n: str) -> bool:
    return 1001 <= int(n) <= 3599


def classify(query: str) -> Route:
    q = re.sub(r"[^\w\s°º]", " ", norm(query))
    q = re.sub(r"\s+", " ", q).strip()
    un_numbers = list(dict.fromkeys(n for n in _UN_RE.findall(q) if _valid_un(n)))[:3]
    guides = list(dict.fromkeys(_GUIDE_RE.findall(q)))[:2]

    if not un_numbers and not guides and any(p.fullmatch(q) for p in _LOW_PATTERNS):
        intent = "gracias" if _THANKS_RE.match(q) else "saludo"
        return Route("low", intent, reason="patrón conversacional")

    scenario = len(set(_SCENARIO.findall(q)))
    aspects = len(set(_ASPECTS.findall(q)))
    event = bool(_EVENT.search(q))
    if (
        (event and scenario >= 1 and scenario + aspects >= 2)
        or aspects >= 3
        or scenario >= 3
    ):
        reason = f"escenario (señales={scenario}, aspectos={aspects})"
        return Route("high", "incidente", un_numbers, guides, reason)
    return Route("medium", "consulta", un_numbers, guides, "consulta puntual")
