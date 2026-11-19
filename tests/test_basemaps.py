"""Capas del mapa según las claves configuradas (sin red: la sesión de Google está simulada)."""

import io
import json
from types import SimpleNamespace

import pytest

from src.geo import basemaps


def _features(esri="", google=""):
    return SimpleNamespace(ESRI_API_KEY=esri, GOOGLE_MAPS_API_KEY=google)


@pytest.fixture(autouse=True)
def clean_sessions():
    basemaps._sessions.clear()


def test_without_keys_only_open_layers(monkeypatch):
    monkeypatch.setattr(basemaps, "features", _features())
    names = [layer.name for layer in basemaps.available_layers()]
    assert names == ["Calles (OpenStreetMap)", "Topográfico (OpenTopoMap)"]


def test_esri_layers_first_with_labels_overlay(monkeypatch):
    monkeypatch.setattr(basemaps, "features", _features(esri="ESRI-KEY-123"))
    layers = basemaps.available_layers()
    assert layers[0].name == "Satélite" and "World_Imagery" in layers[0].url
    assert "imagery/labels" in layers[0].overlay_url
    assert {"Calles", "Noche", "Topográfico"} <= {layer.name for layer in layers}
    assert all(layer.tile_size == 512 for layer in layers if "static-map" in layer.url)
    assert all("ESRI-KEY-123" not in layer.attribution for layer in layers)


def test_google_session_is_cached(monkeypatch):
    calls = []

    def fake_urlopen(req, timeout):
        calls.append(json.loads(req.data))
        body = {"session": "S1", "expiry": "9999999999"}
        return io.BytesIO(json.dumps(body).encode())

    monkeypatch.setattr(basemaps.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(basemaps, "features", _features(google="G-KEY"))
    first = basemaps.available_layers()
    second = basemaps.available_layers()
    google = [layer for layer in first if layer.name.startswith("Google")]
    assert len(google) == 4 and "session=S1" in google[0].url
    assert len(calls) == 4  # una sesión por tipo; la segunda vez sale de la caché
    assert [layer.name for layer in first] == [layer.name for layer in second]
    assert calls[0]["region"] == "CL"
    assert all("G-KEY" not in layer.attribution for layer in google)


def test_google_failure_falls_back(monkeypatch):
    def boom(*a, **k):
        raise OSError("sin red")

    monkeypatch.setattr(basemaps.urllib.request, "urlopen", boom)
    monkeypatch.setattr(basemaps, "features", _features(google="G-KEY"))
    names = [layer.name for layer in basemaps.available_layers()]
    assert names == ["Calles (OpenStreetMap)", "Topográfico (OpenTopoMap)"]


def test_folium_map_uses_layers_and_marks_my_position(monkeypatch):
    from src.ui.zone_folium import build_map

    monkeypatch.setattr(basemaps, "features", _features(esri="K"))
    html = (
        build_map(-41.47, -72.94, None, "N", me=(-41.47, -72.94, 12.0))
        .get_root()
        .render()
    )
    assert "World_Imagery" in html and "Calles y nombres" in html
    assert "Tu ubicación" in html and "Pantalla completa" in html
