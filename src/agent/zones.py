"""Distancias de aislamiento y acción protectora (GRE 2024).

Prioridad de la fuente, como indica la GRE:
1. Material resaltado en la **Tabla 1** → distancias por tamaño de derrame y día/noche.
2. Si la Tabla 1 remite a la **Tabla 3** (derrame grande de gases tóxicos comunes) → se informa así.
3. Material no resaltado → la **guía naranja** ("Aisle … como mínimo N metros" y evacuación a favor del viento).
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import datetime

from src.config.features import features
from src.retrieval.retriever import retriever

_VAL = re.compile(r"(\d+(?:[.,]\d+)?)\s*(km|m)\s*\(")
_ISOLATE = re.compile(r"como m[íi]nimo\s+(\d[\d.]*)\s*metros", re.IGNORECASE)
_DOWNWIND = re.compile(
    r"a favor del viento de por lo menos\s+(\d[\d.]*)\s*metros", re.IGNORECASE
)
_FIRE = re.compile(
    r"incendio,?\s+AISLE\s+(?:a la redonda\s+a\s+)?(\d[\d.]*)\s*metros", re.IGNORECASE
)


@dataclass
class Zones:
    un: str
    material: str
    guide: str
    spill: str  # pequeño | grande
    period: str  # día | noche
    isolate_m: float | None
    protect_km: float | None
    fire_isolate_m: float | None
    method: str  # tabla1 | tabla3 | guia
    page: str
    note: str = ""

    def as_dict(self) -> dict:
        return asdict(self)


def period_for(when: datetime | None = None) -> str:
    hour = (when or datetime.now().astimezone()).hour
    return "día" if features.DAY_START <= hour < features.DAY_END else "noche"


def parse_tabla1(row: str) -> dict:
    """Devuelve {'pequeño': (aislar_m, día_km, noche_km), 'grande': (...) | None}."""
    values = [(float(v.replace(",", ".")), u) for v, u in _VAL.findall(row)]
    out: dict = {"pequeño": None, "grande": None}
    if len(values) >= 3:
        out["pequeño"] = (values[0][0], values[1][0], values[2][0])
    if len(values) >= 6:
        out["grande"] = (values[3][0], values[4][0], values[5][0])
    return out


def _from_guide(guide: str) -> tuple[float | None, float | None, float | None, str]:
    docs = retriever.get_guide(guide)
    text = " ".join(d.get("text", "") for d in docs)
    page = next(
        (
            d["metadata"]["page_label"]
            for d in docs
            if _ISOLATE.search(d.get("text", ""))
        ),
        docs[0]["metadata"]["page_label"] if docs else "",
    )
    iso, down, fire = _ISOLATE.search(text), _DOWNWIND.search(text), _FIRE.search(text)

    def to_float(m):
        return float(m.group(1).replace(".", "")) if m else None

    downwind = to_float(down)
    return to_float(iso), (downwind / 1000 if downwind else None), to_float(fire), page


def zones_for(
    un: str, spill: str = "pequeño", when: datetime | None = None
) -> Zones | None:
    entry = retriever.lookup_un(un)
    if not entry:
        return None
    guide = (entry.get("guides") or [""])[0].rstrip("P")
    material = (entry.get("names") or [""])[0]
    period = period_for(when)
    g_iso, g_down, g_fire, g_page = (
        _from_guide(guide) if guide else (None, None, None, "")
    )
    base = {
        "un": entry["un"],
        "material": material,
        "guide": guide,
        "spill": spill,
        "period": period,
        "fire_isolate_m": g_fire,
    }

    for row in entry.get("tabla1", []):
        parsed = parse_tabla1(row["row"])
        values = parsed.get(spill)
        if values:
            iso, day, night = values
            return Zones(
                **base,
                isolate_m=iso,
                protect_km=day if period == "día" else night,
                method="tabla1",
                page=row["page_label"],
            )
        if spill == "grande" and "tabla 3" in row["row"].lower():
            return Zones(
                **base,
                isolate_m=None,
                protect_km=None,
                method="tabla3",
                page=row["page_label"],
                note="Para derrame grande la GRE remite a la Tabla 3 (según contenedor y viento).",
            )
    return Zones(
        **base,
        isolate_m=g_iso,
        protect_km=g_down if spill == "grande" else None,
        method="guia",
        page=g_page,
        note=""
        if spill == "grande"
        else "Derrame pequeño: aplicar aislamiento inicial de la guía.",
    )
