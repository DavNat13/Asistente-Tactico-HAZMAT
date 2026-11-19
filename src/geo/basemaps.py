"""Capas base del mapa según las claves configuradas (solo servicios oficiales).

- `ESRI_API_KEY` (ArcGIS Location Platform, cuenta gratuita sin tarjeta): satélite World Imagery,
  híbrido (satélite + calles y nombres), navegación diurna y nocturna, y exterior/topográfico.
- `GOOGLE_MAPS_API_KEY` (opcional, Map Tiles API; requiere cuenta de facturación): mapa, satélite,
  relieve y tráfico, con sesión creada en el servidor y guardada en caché.
- Sin claves: OpenStreetMap y OpenTopoMap.
Las claves viajan en la URL de las teselas (así funcionan estos servicios): restríngelas por dominio.
"""

from __future__ import annotations

import json
import logging
import threading
import time
import urllib.request
from dataclasses import dataclass

from src.config.features import features

log = logging.getLogger("hazmat.basemaps")
ESRI_IMAGERY = "https://ibasemaps-api.arcgis.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}?token=%s"
ESRI_STATIC = "https://static-map-tiles-api.arcgis.com/arcgis/rest/services/static-basemap-tiles-service/v1/%s/static/tile/{z}/{y}/{x}?token=%s"
ESRI_ATTR = (
    "Powered by Esri | Esri, Maxar, Airbus, Earthstar Geographics, HERE, OpenStreetMap"
)
GOOGLE_SESSION = "https://tile.googleapis.com/v1/createSession?key=%s"
GOOGLE_TILE = "https://tile.googleapis.com/v1/2dtiles/{z}/{x}/{y}?session=%s&key=%s"
GOOGLE_TYPES = {
    "Google · Mapa": ("roadmap", []),
    "Google · Satélite": ("satellite", ["layerRoadmap"]),
    "Google · Relieve": ("terrain", ["layerRoadmap"]),
    "Google · Tráfico": ("roadmap", ["layerTraffic"]),
}


@dataclass(frozen=True)
class Layer:
    name: str
    url: str
    attribution: str
    tile_size: int = 256
    overlay_url: str | None = None  # p. ej. calles y nombres sobre el satélite
    max_zoom: int = 19


def _esri(key: str) -> list[Layer]:
    labels = ESRI_STATIC % ("arcgis/imagery/labels", key)
    return [
        Layer(
            "Satélite", ESRI_IMAGERY % key, ESRI_ATTR, overlay_url=labels, max_zoom=20
        ),
        Layer("Calles", ESRI_STATIC % ("arcgis/navigation", key), ESRI_ATTR, 512),
        Layer("Noche", ESRI_STATIC % ("arcgis/navigation-night", key), ESRI_ATTR, 512),
        Layer("Topográfico", ESRI_STATIC % ("arcgis/outdoor", key), ESRI_ATTR, 512),
    ]


_sessions: dict[str, tuple[str, float]] = {}
_lock = threading.Lock()


def google_session(key: str, map_type: str, layers: list[str]) -> str | None:
    """Token de sesión de Google (válido ~2 semanas); se renueva 1 día antes de vencer."""
    cache_key = f"{map_type}:{','.join(layers)}"
    with _lock:
        token, expiry = _sessions.get(cache_key, ("", 0.0))
        if token and expiry - time.time() > 86400:
            return token
        body = {"mapType": map_type, "language": "es-419", "region": "CL"}
        if layers:
            body["layerTypes"] = layers
        req = urllib.request.Request(
            GOOGLE_SESSION % key,
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.load(resp)
            _sessions[cache_key] = (data["session"], float(data["expiry"]))
            return data["session"]
        except Exception as e:  # noqa: BLE001 — sin Google se usan las otras capas
            log.warning(
                "No se pudo crear la sesión de Google Maps: %s", type(e).__name__
            )
            return None


def _google(key: str) -> list[Layer]:
    out = []
    for name, (map_type, layers) in GOOGLE_TYPES.items():
        session = google_session(key, map_type, layers)
        if session:
            out.append(
                Layer(
                    name,
                    GOOGLE_TILE % (session, key),
                    "Map data © Google",
                    256,
                    max_zoom=21,
                )
            )
    return out


def _open() -> list[Layer]:
    return [
        Layer(
            "Calles (OpenStreetMap)",
            "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            "© OpenStreetMap contributors",
        ),
        Layer(
            "Topográfico (OpenTopoMap)",
            "https://tile.opentopomap.org/{z}/{x}/{y}.png",
            "© OpenStreetMap contributors, SRTM | © OpenTopoMap (CC-BY-SA)",
            max_zoom=17,
        ),
    ]


def available_layers() -> list[Layer]:
    """Capas en orden de preferencia (la primera es la que se muestra al abrir el mapa)."""
    layers: list[Layer] = []
    if features.ESRI_API_KEY:
        layers += _esri(features.ESRI_API_KEY)
    if features.GOOGLE_MAPS_API_KEY:
        layers += _google(features.GOOGLE_MAPS_API_KEY)
    return layers + _open()
