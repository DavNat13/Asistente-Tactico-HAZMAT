"""Checklist de respuesta por fases a partir de un plan de nivel alto (lógica pura, sin UI).

Las viñetas de cada sección de la respuesta (**Identificación**, **Aislamiento…**, **Acciones…**)
se asignan a fases fijas del procedimiento; las fases sin contenido usan pasos generales de la GRE.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime

PHASES = (
    (
        "aproximacion",
        "Aproximación segura",
        (
            "Acercarse con el viento a favor, desde zona alta y corriente arriba",
            "Establecer el puesto de mando fuera de la zona de peligro",
        ),
    ),
    (
        "identificacion",
        "Identificación",
        ("Confirmar N° UN, guía y estado del contenedor",),
    ),
    (
        "aislamiento",
        "Aislamiento y evacuación",
        ("Aislar el área y prohibir el ingreso de personal no autorizado",),
    ),
    (
        "epp",
        "Equipo de protección",
        ("Verificar ERA de presión positiva y traje adecuado",),
    ),
    ("acciones", "Control de fuego / derrame", ()),
    (
        "auxilios",
        "Primeros auxilios",
        ("Trasladar víctimas a zona fresca y avisar al SAMU (131)",),
    ),
    (
        "cierre",
        "Descontaminación y cierre",
        (
            "Delimitar el corredor de descontaminación",
            "Registrar al personal expuesto",
            "Entregar la escena a la autoridad competente",
        ),
    ),
)
_KEYWORDS = (
    ("aproximacion", r"confirmar|terreno|aproxim"),
    ("identificacion", r"identific|material"),
    ("aislamiento", r"aisla|evacu|distancia"),
    ("epp", r"equipo|epp|epi|protecci|era\b|traje"),
    ("auxilios", r"auxilio|v[ií]ctima"),
    ("cierre", r"descontamin|cierre"),
    ("acciones", r"acci|control|fuego|derrame|incendio|t[aá]ctic"),
)
_HEADING = re.compile(r"^\s*\*\*(.+?)\*\*\s*:?\s*(.*)$")
_ITEM = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+(.+)$")
_MD = re.compile(r"\*\*|\*|`|_")


def _phase_for(heading: str) -> str | None:
    h = heading.lower()
    return next((key for key, pat in _KEYWORDS if re.search(pat, h)), None)


def _clean(text: str) -> str:
    text = re.sub(r"\(\s*GRE[^)]*\)|\*\(GRE[^)]*\)\*", "", text)
    text = re.sub(r"^\((.+?)\)", r"\1", _MD.sub("", text).strip())
    return text.strip(" .;:")[:220]


def parse_plan(answer: str) -> dict[str, list[str]]:
    by_phase: dict[str, list[str]] = {key: [] for key, _, _ in PHASES}
    current: str | None = None
    for line in (answer or "").splitlines():
        heading = _HEADING.match(line)
        if heading and not _ITEM.match(line):
            current = _phase_for(heading.group(1))
            rest = _clean(heading.group(2))
            if current and rest:
                by_phase[current].append(rest)
            continue
        item = _ITEM.match(line)
        if item and current:
            text = _clean(item.group(1))
            if text:
                by_phase[current].append(text)
    return by_phase


def build_incident(answer: str, un: str | None = None, title: str = "") -> dict:
    parsed = parse_plan(answer)
    items = []
    for key, label, defaults in PHASES:
        for text in parsed[key] or list(defaults):
            items.append({"phase": label, "text": text, "done": False, "done_at": None})
    now = datetime.now(UTC).isoformat()
    return {
        "title": title or (f"Incidente UN {un}" if un else "Incidente HAZMAT"),
        "un": un,
        "started_at": now,
        "closed_at": None,
        "items": items,
        "log": [{"at": now, "text": "Inicio del incidente"}],
    }


def toggle(incident: dict, index: int, done: bool) -> dict:
    item = incident["items"][index]
    if item["done"] == done:
        return incident
    now = datetime.now(UTC).isoformat()
    item["done"], item["done_at"] = done, (now if done else None)
    verb = "Completado" if done else "Reabierto"
    incident["log"].append({"at": now, "text": f"{verb}: {item['text'][:90]}"})
    return incident


def progress(incident: dict) -> tuple[int, int]:
    items = incident.get("items", [])
    return sum(1 for i in items if i["done"]), len(items)
