"""Página "Mapa de zonas": aislamiento y acción protectora sobre el lugar real del incidente."""

from __future__ import annotations

import streamlit as st
from streamlit_folium import st_folium

from src.agent.zones import period_for, zones_for
from src.geo.geocode import geocode
from src.geo.geometry import WIND_FROM
from src.ui import state
from src.ui.sidebar import render_sidebar
from src.ui.zone_folium import build_map

DEFAULT_POINT = (-41.4693, -72.9424)  # Puerto Montt


@st.cache_data(ttl=3600, show_spinner=False)
def _geocode(address: str):
    return geocode(address)


def _controls() -> tuple[str, str, str]:
    c1, c2, c3 = st.columns([1.2, 1.4, 1.2], vertical_alignment="bottom")
    un = c1.text_input(
        "N° UN",
        value=st.session_state.get("map_un", "1017"),
        max_chars=4,
        placeholder="ej. 1017",
        icon=":material/tag:",
        key="map_un_input",
    )
    spill = c2.segmented_control(
        "Tamaño del derrame",
        ["pequeño", "grande"],
        default="pequeño",
        required=True,
        format_func=str.capitalize,
        key="map_spill",
    )
    wind = c3.selectbox(
        "Viento desde",
        list(WIND_FROM),
        index=0,
        key="map_wind",
        help="Dirección DESDE la que sopla el viento (la zona se proyecta hacia el lado opuesto).",
    )
    return un.strip(), spill, wind


def _locate() -> tuple[float, float]:
    point = st.session_state.setdefault("map_point", DEFAULT_POINT)
    with st.form("map_search", border=False):
        c1, c2 = st.columns([4, 1], vertical_alignment="bottom")
        address = c1.text_input(
            "Lugar del incidente",
            placeholder="Dirección, comuna o lugar (ej. Ruta 5 Sur km 1020, Puerto Montt)",
            icon=":material/location_on:",
        )
        if (
            c2.form_submit_button("Buscar", icon=":material/search:", width="stretch")
            and address
        ):
            hit = _geocode(address)
            if hit:
                point = st.session_state.map_point = (hit["lat"], hit["lon"])
                st.toast(hit["label"][:120], icon=":material/location_on:")
            else:
                st.warning(
                    "No encontré esa dirección. Prueba con otra o haz clic en el mapa.",
                    icon=":material/search_off:",
                )
    return point


def _summary(z) -> None:
    if not z:
        st.error("No encontré ese N° UN en la GRE 2024.", icon=":material/error:")
        return
    c = st.columns(4)
    c[0].metric(
        "Material", f"UN {z.un}", z.material[:28], delta_color="off", delta_arrow="off"
    )
    c[1].metric("Aislamiento inicial", f"{z.isolate_m:g} m" if z.isolate_m else "—")
    c[2].metric(
        f"Acción protectora ({z.period})",
        f"{z.protect_km:g} km" if z.protect_km else "—",
    )
    c[3].metric(
        "Incendio de tanque", f"{z.fire_isolate_m:g} m" if z.fire_isolate_m else "—"
    )
    source = {"tabla1": "Tabla 1", "tabla3": "Tabla 3", "guia": f"Guía {z.guide}"}[
        z.method
    ]
    st.caption(
        f":material/menu_book: Fuente: GRE 2024 · {source} · página {z.page}. {z.note}"
    )


def zone_map_page() -> None:
    state.init_chat_state()
    render_sidebar(full=False)
    st.html('<div class="hz-dash"></div>')
    st.markdown("## :material/map: Mapa de zonas")
    st.caption(
        f"Distancias de la GRE 2024 sobre el lugar del incidente · ahora es **{period_for()}** "
        "(cambia las distancias de la Tabla 1). Haz clic en el mapa para mover el punto."
    )
    un, spill, wind = _controls()
    lat, lon = _locate()
    z = zones_for(un, spill) if len(un) == 4 and un.isdigit() else None
    _summary(z)
    if z and z.method == "tabla3":
        st.warning(z.note, icon=":material/warning:")
    out = st_folium(
        build_map(lat, lon, z, wind),
        height=540,
        use_container_width=True,
        returned_objects=["last_clicked"],
        key="zone_map",
    )
    clicked = (out or {}).get("last_clicked")
    if clicked and (round(clicked["lat"], 6), round(clicked["lng"], 6)) != (
        round(lat, 6),
        round(lon, 6),
    ):
        st.session_state.map_point = (clicked["lat"], clicked["lng"])
        st.rerun()
    st.caption(
        ":material/info: Herramienta de apoyo: confirma con la GRE impresa y ajusta según el terreno, "
        "el tipo de contenedor y las instrucciones del mando. Las direcciones se buscan en OpenStreetMap."
    )
