"""Estilos y bloques reutilizables de los PDF (texto siempre escapado)."""

from __future__ import annotations

import re
from html import escape

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, Table, TableStyle

RED = colors.HexColor("#c8102e")
INK = colors.HexColor("#1c1917")
MUTED = colors.HexColor("#78716c")
LINE = colors.HexColor("#e7e5e4")
_styles = getSampleStyleSheet()
H1 = ParagraphStyle(
    "h1", parent=_styles["Title"], fontSize=18, textColor=INK, alignment=0, spaceAfter=2
)
H2 = ParagraphStyle(
    "h2",
    parent=_styles["Heading2"],
    fontSize=12,
    textColor=RED,
    spaceBefore=10,
    spaceAfter=4,
)
BODY = ParagraphStyle(
    "b", parent=_styles["BodyText"], fontSize=9.5, leading=13, textColor=INK
)
SMALL = ParagraphStyle("s", parent=BODY, fontSize=8, leading=10, textColor=MUTED)


def _p(text: str, style=BODY) -> Paragraph:
    """Markdown mínimo (**negrita**, *cursiva*) sobre texto escapado."""
    safe = escape(text or "")
    safe = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", safe)
    safe = re.sub(r"(?<!\*)\*(?!\*)(.+?)\*", r"<i>\1</i>", safe)
    return Paragraph(safe, style)


def _table(rows: list[list], widths: list[float]) -> Table:
    t = Table(rows, colWidths=widths, hAlign="LEFT")
    t.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (0, -1), MUTED),
                ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return t
