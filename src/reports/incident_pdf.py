"""Ficha de incidente en PDF (reportlab). Todo texto se escapa antes de entrar a los párrafos."""

from __future__ import annotations

import io
import re
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Spacer

from src.reports.pdf_style import H1, H2, SMALL, _p, _table


def _fmt_time(iso: str | None) -> str:
    if not iso:
        return "—"
    return datetime.fromisoformat(iso).astimezone().strftime("%d/%m %H:%M")


def _answer_blocks(answer: str) -> list:
    blocks = []
    for line in (answer or "").splitlines():
        line = line.strip()
        if not line or line == "---":
            continue
        bullet = re.match(r"^(?:[-*•]|\d+[.)])\s+(.*)", line)
        blocks.append(_p(("• " + bullet.group(1)) if bullet else line))
    return blocks


def build_incident_pdf(data: dict) -> bytes:
    """data: title, user, answer, sources[], zones{}|None, incident{}|None."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="Ficha de incidente HAZMAT",
        author="Asistente HAZMAT",
    )
    now = datetime.now().astimezone().strftime("%d/%m/%Y %H:%M")
    story = [
        _p("ASISTENTE HAZMAT · BOMBEROS DE CHILE", SMALL),
        _p(data.get("title") or "Ficha de incidente", H1),
        _p(f"Generada el {now} por {data.get('user', '—')}", SMALL),
        Spacer(1, 6),
    ]
    z = data.get("zones")
    if z:
        story += [
            _p("Distancias (GRE 2024)", H2),
            _table(
                [
                    ["Material", f"UN {z['un']} · {z['material']} · Guía {z['guide']}"],
                    [
                        "Aislamiento inicial",
                        f"{z['isolate_m']:g} m" if z.get("isolate_m") else "Ver nota",
                    ],
                    [
                        f"Acción protectora ({z['period']})",
                        f"{z['protect_km']:g} km"
                        if z.get("protect_km")
                        else "No aplica / ver nota",
                    ],
                    [
                        "Incendio de tanque",
                        f"{z['fire_isolate_m']:g} m"
                        if z.get("fire_isolate_m")
                        else "—",
                    ],
                    [
                        "Fuente",
                        f"GRE 2024, página {z['page']} ({z['method']}). {z.get('note', '')}",
                    ],
                ],
                [45 * mm, 125 * mm],
            ),
        ]
    story += [_p("Plan de respuesta", H2), *_answer_blocks(data.get("answer", ""))]
    inc = data.get("incident")
    if inc:
        rows = [
            [
                ("Hecho" if i["done"] else "Pendiente"),
                i["phase"],
                i["text"],
                _fmt_time(i.get("done_at")),
            ]
            for i in inc["items"]
        ]
        story += [
            _p("Checklist", H2),
            _table(
                [[_p(r[0], SMALL), _p(r[1], SMALL), _p(r[2]), r[3]] for r in rows],
                [18 * mm, 32 * mm, 98 * mm, 22 * mm],
            ),
        ]
        story += [_p("Bitácora", H2)] + [
            _p(f"{_fmt_time(e['at'])} — {e['text']}", SMALL) for e in inc["log"][-40:]
        ]
    sources = data.get("sources") or []
    if sources:
        story += [
            _p("Fuentes consultadas", H2),
            _p(" · ".join(f"{s['source']} p. {s['page']}" for s in sources), SMALL),
        ]
    story += [
        Spacer(1, 10),
        _p(
            "Herramienta de apoyo a la decisión basada en la GRE 2024. Verifique en la guía impresa y siga "
            "las instrucciones del mando del incidente.",
            SMALL,
        ),
    ]
    doc.build(story)
    return buf.getvalue()
