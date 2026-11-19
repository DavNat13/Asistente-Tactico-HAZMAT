"""Semáforo de observabilidad, gráficos sin solapes, componentes de UI y GPS."""

import math

import pandas as pd
import pytest

from src.observability import health_status
from src.ui import charts
from src.ui.geolocate import parse_position
from src.ui.ui_kit import stat_tile


def _runs(n=10, latency_s=2.0, errors=0, blocked=0):
    return pd.DataFrame(
        {
            "status": ["error"] * errors + ["ok"] * (n - errors),
            "latency_ms": [latency_s * 1000] * n,
            "blocked": [True] * blocked + [False] * (n - blocked),
        }
    )


def test_overall_states():
    assert health_status.overall(pd.DataFrame())[0] == "neutral"
    assert health_status.overall(_runs())[0] == "ok"
    assert health_status.overall(_runs(latency_s=999))[0] == "warn"
    state, title, lines = health_status.overall(_runs(errors=5))
    assert (
        state == "crit" and title == "Requiere acción" and "error" in lines[0].lower()
    )


@pytest.mark.parametrize(
    ("kpis", "key", "expected"),
    [
        ({"p95": 5.0}, "p95", "ok"),
        ({"p95": 25.0}, "p95", "warn"),
        ({"p95": 99.0}, "p95", "crit"),
        ({"p95": None}, "p95", "neutral"),
        ({"error_rate": 0.0}, "error_rate", "ok"),
        ({"error_rate": 0.5}, "error_rate", "crit"),
        ({"grounded": 1.0}, "grounded", "ok"),
        ({"grounded": 0.5}, "grounded", "crit"),
        ({"feedback_pos": float("nan")}, "feedback_pos", "neutral"),
    ],
)
def test_kpi_states(kpis, key, expected):
    assert health_status.kpi_states(kpis)[key] == expected


def test_hbar_uses_step_height_and_shared_order():
    df = pd.DataFrame({"kind": ["a", "b", "c"], "n": [1, 5, 3]})
    spec = charts.hbar(df, "kind", "n", "eventos").to_dict()
    assert spec["height"] == {"step": 34}  # alto por fila → etiquetas sin superponerse
    sorts = [layer["encoding"]["y"]["sort"] for layer in spec["layer"]]
    assert sorts[0] == sorts[1] == ["b", "c", "a"]


def test_stat_tile_escapes_and_marks_state():
    out = stat_tile("<b>x</b>", "1", "crit", hint="<script>")
    assert "<script>" not in out and "&lt;b&gt;" in out and "hz-crit" in out


@pytest.mark.parametrize(
    ("value", "ok"),
    [
        ({"lat": -41.47, "lon": -72.94, "accuracy": 12}, True),
        ({"lat": 91, "lon": 0}, False),
        ({"lat": 0, "lon": 200}, False),
        ({"lat": "x", "lon": 0}, False),
        ({"lat": 0, "lon": 0, "accuracy": math.inf}, False),
        (None, False),
    ],
)
def test_parse_position(value, ok):
    assert (parse_position(value) is not None) == ok
