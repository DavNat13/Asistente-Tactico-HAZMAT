"""Componentes del sistema de diseño "Centro de mando": encabezado de página, tarjetas, indicadores
con semáforo, banda de estado y estados vacíos. Todo texto dinámico se escapa con html.escape.
"""

from __future__ import annotations

import html
from contextlib import contextmanager

import streamlit as st

from src.ui.icons import ACCENT, WHITE, icon

STATES = ("ok", "warn", "crit", "info", "neutral")
STATE_COLORS = {
    "ok": "#16a34a",
    "warn": "#d97706",
    "crit": "#dc2626",
    "info": "#2563eb",
    "neutral": "#8a847c",
}
STATE_LABELS = {
    "ok": "Operativo",
    "warn": "Atención",
    "crit": "Crítico",
    "info": "Información",
    "neutral": "Sin datos",
}


def _e(text: object) -> str:
    return html.escape(str(text))


def page_header(icon_name: str, title: str, subtitle: str, kicker: str = "") -> None:
    kick = f'<span class="hz-kicker">{_e(kicker)}</span>' if kicker else ""
    st.html(
        f'<div class="hz-page-head"><div class="hz-page-badge">{icon(icon_name, WHITE, 22)}</div>'
        f"<div>{kick}<h1>{_e(title)}</h1><p>{_e(subtitle)}</p></div></div>"
    )


def stat_tile(
    label: str,
    value: str,
    state: str = "neutral",
    detail: str = "",
    icon_name: str = "activity",
    hint: str = "",
) -> str:
    """HTML de un indicador. `hint` explica qué significa (visible al pasar el cursor y para lectores)."""
    state = state if state in STATES else "neutral"
    color = STATE_COLORS[state]
    tip = f' title="{_e(hint)}"' if hint else ""
    sr = f'<span class="hz-sr">{_e(hint)}</span>' if hint else ""
    return (
        f'<div class="hz-tile hz-{state}"{tip}><div class="hz-tile-top">'
        f"<i>{icon(icon_name, color, 16)}</i><span>{_e(label)}</span>"
        f'<em class="hz-dot-live" aria-label="{STATE_LABELS[state]}"></em></div>'
        f"<b>{_e(value)}</b><small>{_e(detail)}</small>{sr}</div>"
    )


def tiles(items: list[str]) -> None:
    st.html(f'<div class="hz-tiles">{"".join(items)}</div>')


def status_banner(state: str, title: str, lines: list[str]) -> None:
    state = state if state in STATES else "neutral"
    items = "".join(f"<li>{_e(line)}</li>" for line in lines)
    name = {"ok": "check", "warn": "alert", "crit": "alert"}.get(state, "activity")
    st.html(
        f'<div class="hz-banner hz-{state}" role="status"><div class="hz-banner-ico">'
        f"{icon(name, STATE_COLORS[state], 22)}</div><div><span>{STATE_LABELS[state]}</span>"
        f"<b>{_e(title)}</b><ul>{items}</ul></div></div>"
    )


@contextmanager
def card(key: str, title: str = "", subtitle: str = "", help_text: str = ""):
    """Tarjeta con borde, sombra y animación. `help_text` agrega el botón "¿Qué significa?"."""
    with st.container(key=f"hzcard_{key}"):
        if title:
            head, aid = st.columns([1, 0.12], vertical_alignment="center")
            sub = f"<p>{_e(subtitle)}</p>" if subtitle else ""
            head.html(f'<div class="hz-card-head"><h3>{_e(title)}</h3>{sub}</div>')
            if help_text:
                with aid.popover("", icon=":material/help:", help="¿Qué significa?"):
                    st.markdown(help_text)
        yield


def empty_state(text: str, icon_name: str = "check") -> None:
    st.html(
        f'<div class="hz-empty">{icon(icon_name, ACCENT, 26)}<p>{_e(text)}</p></div>'
    )


def pill(text: str, state: str = "neutral") -> str:
    state = state if state in STATES else "neutral"
    return f'<span class="hz-pill hz-{state}">{_e(text)}</span>'
