"""Geometría de las zonas de la GRE sobre la esfera terrestre.

- Zona de aislamiento inicial: círculo de radio `isolate_m` alrededor del derrame.
- Zona de acción protectora: según la GRE, un CUADRADO cuyo largo y ancho igualan la distancia
  a favor del viento, con el derrame en el centro del lado que mira hacia el viento.
"""

from __future__ import annotations

import math

EARTH_R = 6_371_000.0
WIND_FROM = {
    "N": 0,
    "NE": 45,
    "E": 90,
    "SE": 135,
    "S": 180,
    "SO": 225,
    "O": 270,
    "NO": 315,
}


def destination(
    lat: float, lon: float, bearing_deg: float, distance_m: float
) -> tuple[float, float]:
    """Punto a `distance_m` metros desde (lat, lon) con rumbo `bearing_deg` (0 = norte)."""
    phi1, lam1, theta = math.radians(lat), math.radians(lon), math.radians(bearing_deg)
    delta = distance_m / EARTH_R
    phi2 = math.asin(
        math.sin(phi1) * math.cos(delta)
        + math.cos(phi1) * math.sin(delta) * math.cos(theta)
    )
    lam2 = lam1 + math.atan2(
        math.sin(theta) * math.sin(delta) * math.cos(phi1),
        math.cos(delta) - math.sin(phi1) * math.sin(phi2),
    )
    return math.degrees(phi2), (math.degrees(lam2) + 540) % 360 - 180


def protective_square(
    lat: float, lon: float, wind_from_deg: float, distance_m: float
) -> list[tuple[float, float]]:
    """Vértices del cuadrado de acción protectora (sentido horario)."""
    downwind = (wind_from_deg + 180) % 360
    half = distance_m / 2
    left = destination(lat, lon, (downwind - 90) % 360, half)
    right = destination(lat, lon, (downwind + 90) % 360, half)
    far_left = destination(*left, downwind, distance_m)
    far_right = destination(*right, downwind, distance_m)
    return [left, far_left, far_right, right]


def haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    (lat1, lon1), (lat2, lon2) = a, b
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dlam = p2 - p1, math.radians(lon2 - lon1)
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlam / 2) ** 2
    return 2 * EARTH_R * math.asin(math.sqrt(h))
