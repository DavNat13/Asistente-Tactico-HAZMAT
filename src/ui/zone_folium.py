"""Construcción del mapa folium con las zonas de aislamiento y de acción protectora."""

from __future__ import annotations

import folium

from src.agent.zones import Zones
from src.geo.geometry import WIND_FROM, destination, protective_square

RED = "#c8102e"
ORANGE = "#eb6834"


def _arrow(
    lat: float, lon: float, wind_from: str, length_m: float
) -> list[tuple[float, float]]:
    downwind = (WIND_FROM[wind_from] + 180) % 360
    return [(lat, lon), destination(lat, lon, downwind, length_m)]


def build_map(lat: float, lon: float, z: Zones | None, wind_from: str) -> folium.Map:
    protect_m = (z.protect_km or 0) * 1000 if z else 0
    isolate_m = (z.isolate_m or 0) if z else 0
    zoom = (
        16
        if protect_m < 400
        else 15
        if protect_m < 1200
        else 13
        if protect_m < 4000
        else 12
    )
    m = folium.Map(
        location=[lat, lon],
        zoom_start=zoom,
        tiles="CartoDB positron",
        control_scale=True,
    )
    folium.TileLayer("OpenStreetMap", name="Calles").add_to(m)

    if protect_m:
        folium.Polygon(
            protective_square(lat, lon, WIND_FROM[wind_from], protect_m),
            color=ORANGE,
            weight=2,
            fill=True,
            fill_opacity=0.18,
            tooltip=f"Acción protectora a favor del viento: {z.protect_km:g} km ({z.period})",
        ).add_to(m)
        folium.PolyLine(
            _arrow(lat, lon, wind_from, protect_m * 0.6),
            color=ORANGE,
            weight=3,
            dash_array="6 6",
            tooltip=f"Viento desde el {wind_from}",
        ).add_to(m)
    if isolate_m:
        folium.Circle(
            [lat, lon],
            radius=isolate_m,
            color=RED,
            weight=2,
            fill=True,
            fill_opacity=0.22,
            tooltip=f"Aislamiento inicial: {isolate_m:g} m a la redonda",
        ).add_to(m)
    if z and z.fire_isolate_m:
        folium.Circle(
            [lat, lon],
            radius=z.fire_isolate_m,
            color=RED,
            weight=1,
            dash_array="4 8",
            fill=False,
            tooltip=f"Si hay incendio de tanque: aislar {z.fire_isolate_m:g} m",
        ).add_to(m)
    folium.Marker(
        [lat, lon],
        tooltip="Punto del derrame (haz clic en el mapa para moverlo)",
        icon=folium.Icon(color="red", icon="warning-sign"),
    ).add_to(m)
    folium.LayerControl(collapsed=True).add_to(m)
    return m
