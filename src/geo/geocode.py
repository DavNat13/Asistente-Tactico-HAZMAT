"""Geocodificación de direcciones con Nominatim (OpenStreetMap).

Política de uso de Nominatim: User-Agent identificable genérico (sin datos del usuario), máximo
1 solicitud por segundo y caché de resultados. Solo se envía el texto de la dirección.
"""

from __future__ import annotations

import json
import logging
import threading
import time
import urllib.parse
import urllib.request
from functools import lru_cache

from src.config.features import features

log = logging.getLogger("hazmat.geo")
USER_AGENT = "AsistenteHAZMAT/5.2 (proyecto academico)"
_lock = threading.Lock()
_last_call = 0.0


def _throttle() -> None:
    global _last_call
    with _lock:
        wait = 1.0 - (time.time() - _last_call)
        if wait > 0:
            time.sleep(wait)
        _last_call = time.time()


@lru_cache(maxsize=256)
def geocode(address: str) -> dict | None:
    """Devuelve {"lat", "lon", "label"} o None si no hay resultados."""
    address = (address or "").strip()[:200]
    if len(address) < 4:
        return None
    params = urllib.parse.urlencode(
        {
            "q": address,
            "format": "json",
            "limit": 1,
            "countrycodes": features.GEOCODER_COUNTRY,
        }
    )
    req = urllib.request.Request(
        f"{features.GEOCODER_URL}?{params}", headers={"User-Agent": USER_AGENT}
    )
    _throttle()
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (OSError, ValueError) as e:
        log.warning("Geocodificación no disponible: %s", type(e).__name__)
        return None
    if not data:
        return None
    hit = data[0]
    return {
        "lat": float(hit["lat"]),
        "lon": float(hit["lon"]),
        "label": hit.get("display_name", address),
    }
