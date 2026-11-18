"""Herramientas de terreno: Tabla 1, geometría de zonas, visión, checklist y ficha PDF."""

from datetime import UTC, datetime

import pytest

from src.agent import zones
from src.agent.checklist import build_incident, parse_plan, progress, toggle
from src.agent.vision import ImageError, parse_vision, prepare_image
from src.geo.geometry import haversine_m, protective_square
from src.reports.incident_pdf import build_incident_pdf

ROW_CLORO = (
    "1017 124 Cloro 60 m (200 pies) 0.3 km (0.2 mi) 1.5 km (0.9 mi) Consulte la Tabla 3"
)
ROW_BORO = (
    "1008 125 Trifluoruro de boro 30 m (100 pies) 0.2 km (0.1 mi) 0.7 km (0.5 mi) "
    "400 m (1250 pies) 2.4 km (1.5 mi) 4.7 km (2.9 mi)"
)


def test_parse_tabla1_rows():
    assert zones.parse_tabla1(ROW_CLORO) == {
        "pequeño": (60.0, 0.3, 1.5),
        "grande": None,
    }
    assert zones.parse_tabla1(ROW_BORO)["grande"] == (400.0, 2.4, 4.7)


@pytest.mark.parametrize(("hour", "period"), [(12, "día"), (6, "noche"), (23, "noche")])
def test_period(hour, period):
    assert zones.period_for(datetime(2026, 11, 17, hour, tzinfo=UTC)) == period


@pytest.fixture
def fake_retriever(monkeypatch):
    class R:
        def lookup_un(self, un):
            if un == "1017":
                return {
                    "un": "1017",
                    "guides": ["124"],
                    "names": ["Cloro"],
                    "tabla1": [{"row": ROW_CLORO, "page_label": "296"}],
                }
            if un == "1203":
                return {"un": "1203", "guides": ["128"], "names": ["Gasolina"]}
            return None

        def get_guide(self, g):
            text = (
                "Aisle el área del derrame o escape como mínimo 50 metros (150 pies). Considere la "
                "evacuación inicial a favor del viento de por lo menos 300 metros (1000 pies). Si un "
                "tanque está involucrado en un incendio, AISLE 800 metros (1/2 milla)"
            )
            return [{"text": text, "metadata": {"page_label": "190"}}]

    monkeypatch.setattr(zones, "retriever", R())


def test_zones_tabla1_day_night(fake_retriever):
    day = zones.zones_for("1017", "pequeño", datetime(2026, 1, 1, 12, tzinfo=UTC))
    night = zones.zones_for("1017", "pequeño", datetime(2026, 1, 1, 23, tzinfo=UTC))
    assert (day.isolate_m, day.protect_km, day.method, day.page) == (
        60.0,
        0.3,
        "tabla1",
        "296",
    )
    assert night.protect_km == 1.5
    assert zones.zones_for("1017", "grande").method == "tabla3"


def test_zones_from_guide(fake_retriever):
    z = zones.zones_for("1203", "grande", datetime(2026, 1, 1, 12, tzinfo=UTC))
    assert (z.isolate_m, z.protect_km, z.fire_isolate_m, z.method) == (
        50.0,
        0.3,
        800.0,
        "guia",
    )
    assert zones.zones_for("9999") is None


def test_protective_square_geometry():
    center = (-41.4693, -72.9424)
    sq = protective_square(
        *center, wind_from_deg=0, distance_m=1000
    )  # viento desde el norte
    assert len(sq) == 4
    assert all(p[0] <= center[0] + 1e-5 for p in sq)  # la zona queda al SUR del derrame
    assert haversine_m(sq[0], sq[3]) == pytest.approx(
        1000, rel=0.01
    )  # ancho = distancia
    assert haversine_m(sq[0], sq[1]) == pytest.approx(
        1000, rel=0.01
    )  # largo = distancia


def test_vision_parse_only_keeps_safe_digits():
    assert parse_vision('{"un": "1203", "confianza": "alta"}')["un"] == "1203"
    hostile = '{"un": "ignora todo 9999", "confianza": "TOTAL", "descripcion": "<script>x</script>"}'
    out = parse_vision(hostile)
    assert (
        out["un"] is None
        and out["confianza"] == "baja"
        and "<" not in out["descripcion"]
    )
    assert parse_vision("no es json")["un"] is None


def test_prepare_image_rejects_non_images():
    with pytest.raises(ImageError):
        prepare_image(b"%PDF-1.4 no soy una imagen")


PLAN = """**Identificación** (Cloro, UN 1017, Guía 124) *(GRE 2024, p. 182)*
**Aislamiento y evacuación**
- Aislar **60 m** *(GRE 2024, p. 296)*
**Acciones inmediatas**
1. Usar rocío de agua
**Confirmar en terreno**
- Dirección del viento"""


def test_checklist_from_plan():
    parsed = parse_plan(PLAN)
    assert parsed["aislamiento"] == ["Aislar 60 m"]
    assert parsed["acciones"] == ["Usar rocío de agua"]
    assert parsed["aproximacion"] == ["Dirección del viento"]
    inc = build_incident(PLAN, "1017")
    assert progress(inc) == (0, len(inc["items"]))
    toggle(inc, 0, True)
    assert progress(inc)[0] == 1 and inc["log"][-1]["text"].startswith("Completado")


def test_incident_pdf_is_valid_and_escapes_text():
    pdf = build_incident_pdf(
        {
            "title": "<script>Prueba</script>",
            "user": "Test",
            "answer": PLAN,
            "sources": [{"source": "GRE 2024", "page": "296"}],
            "zones": None,
            "incident": build_incident(PLAN, "1017"),
        }
    )
    assert pdf.startswith(b"%PDF") and len(pdf) > 2000
