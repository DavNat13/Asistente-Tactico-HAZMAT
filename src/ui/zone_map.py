"""Página "Mapa de zonas": aislamiento y acción protectora sobre el lugar real del incidente."""

from __future__ import annotations

import streamlit as st
from streamlit_folium import st_folium

from src.agent.zones import period_for, zones_for
from src.geo.geocode import geocode
from src.geo.geometry import WIND_FROM
from src.ui import state
from src.ui.geolocate import geolocate
from src.ui.sidebar import render_sidebar
from src.ui.ui_kit import card, page_header
from src.ui.zone_folium import build_map
from src.ui.zone_summary import zone_summary

DEFAULT_POINT = (-41.4693, -72.9424)  # Puerto Montt


@st.cache_data(ttl=3600, show_spinner=False)
def _geocode(address: str):
    return geocode(address)


def _controls() -> tuple[str, str, str]:
    un = st.text_input(
        "N° UN",
        value=st.session_state.get("map_un", "1017"),
        max_chars=4,
        placeholder="ej. 1017",
        icon=":material/tag:",
        key="map_un_input",
    )
    spill = st.segmented_control(
        "Tamaño del derrame",
        ["pequeño", "grande"],
        default="pequeño",
        required=True,
        format_func=str.capitalize,
        key="map_spill",
        width="stretch",
    )
    wind = st.selectbox(
        "Viento desde",
        list(WIND_FROM),
        index=0,
        key="map_wind",
        help="Dirección DESDE la que sopla el viento (la zona se proyecta hacia el lado opuesto).",
    )
    return un.strip(), spill, wind


def _locate() -> tuple[float, float]:
    point = st.session_state.setdefault("map_point", DEFAULT_POINT)
    st.html('<p class="hz-label">Lugar del incidente</p>')
    me = geolocate("map_geo")
    if me:
        st.session_state.map_me = me
        point = st.session_state.map_point = (me[0], me[1])
        if me[2] > 100:
            st.warning(
                f"Precisión baja (±{me[2]:.0f} m): confirma el punto en el mapa.",
                icon=":material/gps_not_fixed:",
            )
    with st.form("map_search", border=False):
        address = st.text_input(
            "Buscar dirección",
            placeholder="ej. Ruta 5 Sur km 1020, Puerto Montt",
            icon=":material/location_on:",
            label_visibility="collapsed",
        )
        if (
            st.form_submit_button("Buscar", icon=":material/search:", width="stretch")
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


def zone_map_page() -> None:
    state.init_chat_state()
    render_sidebar(full=False)
    st.html('<div class="hz-dash hz-map-page"></div>')
    page_header(
        "map",
        "Mapa de zonas",
        f"Distancias de la GRE 2024 sobre el lugar real · ahora es {period_for()} "
        "(cambia la Tabla 1). Haz clic en el mapa para mover el punto.",
        kicker="Respuesta en terreno",
    )
    left, right = st.columns([1, 2.3], gap="medium")
    with left, card("map_controls", "Incidente"):
        un, spill, wind = _controls()
        lat, lon = _locate()
    z = zones_for(un, spill) if len(un) == 4 and un.isdigit() else None
    with right, card("map_canvas"):
        if z and z.method == "tabla3":
            st.warning(z.note, icon=":material/warning:")
        out = st_folium(
            build_map(lat, lon, z, wind, st.session_state.get("map_me")),
            height=600,
            use_container_width=True,
            returned_objects=["last_clicked"],
            key="zone_map",
        )
    zone_summary(z)
    clicked = (out or {}).get("last_clicked")
    if clicked and (round(clicked["lat"], 6), round(clicked["lng"], 6)) != (
        round(lat, 6),
        round(lon, 6),
    ):
        st.session_state.map_point = (clicked["lat"], clicked["lng"])
        st.rerun()
    st.caption(
        ":material/info: Herramienta de apoyo: confirma con la GRE impresa y ajusta según el "
        "terreno, el tipo de contenedor y las instrucciones del mando. Mapas: Esri/Google si están "
        "configurados, si no OpenStreetMap; las direcciones se buscan en OpenStreetMap."
    )
