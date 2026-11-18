"""Plantillas HTML de correo (estilos en línea: compatibles con Gmail y Outlook).

Todo valor dinámico se escapa con html.escape antes de insertarse.
"""

from __future__ import annotations

import html

from src.config.features import features

ACCENT = "#c8102e"


def layout(title: str, body: str, cta: tuple[str, str] | None = None) -> str:
    button = ""
    if cta:
        label, url = cta
        button = (
            f'<p style="margin:24px 0 8px"><a href="{html.escape(url)}" style="background:{ACCENT};'
            "color:#fff;text-decoration:none;padding:12px 20px;border-radius:10px;font-weight:600;"
            f'display:inline-block">{html.escape(label)}</a></p>'
        )
    return (
        '<div style="background:#f5f5f4;padding:32px 12px;font-family:Inter,Segoe UI,Arial,sans-serif">'
        '<div style="max-width:560px;margin:0 auto;background:#fff;border-radius:16px;overflow:hidden;'
        'box-shadow:0 8px 30px rgba(0,0,0,.08)">'
        f'<div style="background:linear-gradient(135deg,#7a0c1c,{ACCENT},#e2483d);padding:22px 28px;'
        'color:#fff;font-weight:700;font-size:16px">Asistente HAZMAT · Bomberos de Chile</div>'
        f'<div style="padding:28px;color:#1c1917;font-size:15px;line-height:1.6">'
        f'<h2 style="margin:0 0 12px;font-size:20px">{html.escape(title)}</h2>{body}{button}</div>'
        '<div style="padding:16px 28px;background:#fafaf9;color:#78716c;font-size:12px">'
        "Mensaje automático. Herramienta de apoyo: no reemplaza al mando del incidente.</div>"
        "</div></div>"
    )


def paragraph(text: str) -> str:
    return f'<p style="margin:0 0 12px">{html.escape(text)}</p>'


def table(rows: list[tuple[str, str]]) -> str:
    cells = "".join(
        f'<tr><td style="padding:8px 0;color:#78716c;width:55%">{html.escape(str(k))}</td>'
        f'<td style="padding:8px 0;font-weight:600;text-align:right">{html.escape(str(v))}</td></tr>'
        for k, v in rows
    )
    return f'<table style="width:100%;border-collapse:collapse;margin:8px 0 4px">{cells}</table>'


def app_link() -> tuple[str, str]:
    return ("Abrir el Asistente HAZMAT", features.APP_URL)
