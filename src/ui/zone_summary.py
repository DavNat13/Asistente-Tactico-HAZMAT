"""Tarjetas de distancias del mapa de zonas (aislamiento, acción protectora e incendio)."""

from __future__ import annotations

import streamlit as st

from src.ui.ui_kit import empty_state, stat_tile, tiles


def zone_summary(z) -> None:
    if not z:
        empty_state("No encontré ese N° UN en la GRE 2024.", "alert")
        return
    tiles(
        [
            stat_tile("Material", f"UN {z.un}", "info", z.material[:34], "file"),
            stat_tile(
                "Aislamiento inicial",
                f"{z.isolate_m:g} m" if z.isolate_m else "—",
                "crit",
                "a la redonda",
                "crosshair",
            ),
            stat_tile(
                f"Acción protectora ({z.period})",
                f"{z.protect_km:g} km" if z.protect_km else "—",
                "warn",
                "a favor del viento",
                "layers",
            ),
            stat_tile(
                "Incendio de tanque",
                f"{z.fire_isolate_m:g} m" if z.fire_isolate_m else "—",
                "crit",
                "aislar en todas direcciones",
                "alert",
            ),
        ]
    )
    source = {"tabla1": "Tabla 1", "tabla3": "Tabla 3", "guia": f"Guía {z.guide}"}[
        z.method
    ]
    st.caption(f":material/menu_book: GRE 2024 · {source} · página {z.page}. {z.note}")
