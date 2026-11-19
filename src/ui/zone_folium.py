"""Construcción del mapa folium con las zonas de aislamiento y de acción protectora."""

from __future__ import annotations

import folium
from folium.plugins import Fullscreen, MeasureControl

from src.agent.zones import Zones
from src.geo.basemaps import available_layers
from src.geo.geometry import WIND_FROM, destination, protective_square

RED = "#c8102e"
ORANGE = "#eb6834"
BLUE = "#2563eb"


def _arrow(
    lat: float, lon: float, wind_from: str, length_m: float
) -> list[tuple[float, float]]:
    downwind = (WIND_FROM[wind_from] + 180) % 360
    return [(lat, lon), destination(lat, lon, downwind, length_m)]


def _base_layers(m: folium.Map) -> None:
    """Capas oficiales disponibles (Esri / Google / OpenStreetMap); la primera queda visible."""
    overlay = None
    for i, layer in enumerate(available_layers()):
        big = layer.tile_size == 512
        folium.TileLayer(
            tiles=layer.url,
            attr=layer.attribution,
            name=layer.name,
            max_zoom=layer.max_zoom,
            max_native_zoom=layer.max_zoom,
            tile_size=layer.tile_size,
            zoom_offset=-1 if big else 0,
            show=i == 0,
            overlay=False,
            control=True,
        ).add_to(m)
        overlay = overlay or layer.overlay_url
    if overlay:  # calles y nombres sobre el satélite (híbrido); se puede desactivar
        folium.TileLayer(
            tiles=overlay,
            attr="Esri",
            name="Calles y nombres",
            overlay=True,
            show=True,
            tile_size=512,
            zoom_offset=-1,
        ).add_to(m)


def _me(m: folium.Map, me: tuple[float, float, float]) -> None:
    lat, lon, acc = me
    folium.Circle(
        [lat, lon],
        radius=max(acc, 5),
        color=BLUE,
        weight=1,
        fill=True,
        fill_opacity=0.12,
        tooltip=f"Tu ubicación (precisión ±{acc:.0f} m)",
    ).add_to(m)
    folium.CircleMarker(
        [lat, lon],
        radius=7,
        color="#ffffff",
        weight=3,
        fill=True,
        fill_color=BLUE,
        fill_opacity=1,
        tooltip="Tu ubicación",
    ).add_to(m)


def build_map(
    lat: float,
    lon: float,
    z: Zones | None,
    wind_from: str,
    me: tuple[float, float, float] | None = None,
) -> folium.Map:
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
    m = folium.Map(location=[lat, lon], zoom_start=zoom, tiles=None, control_scale=True)
    _base_layers(m)
    Fullscreen(title="Pantalla completa", title_cancel="Salir").add_to(m)
    MeasureControl(
        primary_length_unit="meters",
        secondary_length_unit="kilometers",
        position="topleft",
    ).add_to(m)

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
    if me:
        _me(m, me)
    folium.LayerControl(collapsed=False, position="topright").add_to(m)
    return m
