"""Ubicación del dispositivo en tiempo real (API de geolocalización del navegador).

Componente `st.components.v2` con código fijo del proyecto (sin datos del usuario en el HTML/JS):
- "Usar mi ubicación": una lectura de alta precisión.
- "Seguir en vivo": `watchPosition`; envía una posición nueva solo si se movió > 10 m o pasaron 15 s.
El navegador pide permiso y solo funciona en HTTPS o en localhost. La ubicación no se guarda en la
base de datos: vive en la sesión del navegador.
"""

from __future__ import annotations

import math

import streamlit as st

_HTML = """
<div class="geo">
  <button id="once" type="button"><span>◎</span> Usar mi ubicación</button>
  <button id="live" type="button" aria-pressed="false"><span class="dot"></span> Seguir en vivo</button>
  <small id="msg" role="status"></small>
</div>
"""
_CSS = """
.geo { display: flex; flex-wrap: wrap; gap: .5rem; align-items: center; font-family: inherit; }
button { font: 600 .85rem/1 Inter, system-ui, sans-serif; padding: .6rem .9rem; border-radius: 999px; cursor: pointer;
  border: 1px solid rgb(200 16 46 / .45); background: rgb(200 16 46 / .1); color: var(--st-text-color, inherit);
  display: inline-flex; gap: .45rem; align-items: center; transition: transform .2s, background .2s; }
button:hover { transform: translateY(-1px); background: rgb(200 16 46 / .18); }
button:focus-visible { outline: 3px solid rgb(200 16 46 / .45); outline-offset: 2px; }
#once { background: linear-gradient(135deg, #c8102e, #e2483d); color: #fff; border: none; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; opacity: .45; }
#live[aria-pressed="true"] .dot { background: #16a34a; opacity: 1; animation: b 1.6s infinite; }
@keyframes b { 50% { box-shadow: 0 0 0 6px rgb(22 163 74 / 0); } 0% { box-shadow: 0 0 0 0 rgb(22 163 74 / .6); } }
small { width: 100%; font-size: .78rem; opacity: .8; color: var(--st-text-color, inherit); }
"""
_JS = """
export default function (component) {
  const { parentElement, setTriggerValue } = component;
  const $ = (id) => parentElement.querySelector('#' + id);
  const msg = (t) => { $('msg').textContent = t; };
  const opts = { enableHighAccuracy: true, timeout: 15000, maximumAge: 5000 };
  let last = null;
  const send = (p) => {
    const c = p.coords, now = Date.now();
    if (last) {
      const d = Math.hypot((c.latitude - last.lat) * 111320, (c.longitude - last.lon) * 111320 * Math.cos(c.latitude * Math.PI / 180));
      if (d < 10 && now - last.ts < 15000) return;
    }
    last = { lat: c.latitude, lon: c.longitude, ts: now };
    msg('Precisión ±' + Math.round(c.accuracy) + ' m');
    setTriggerValue('position', { lat: c.latitude, lon: c.longitude, accuracy: c.accuracy, ts: now });
  };
  const fail = (e) => {
    const t = { 1: 'Permiso de ubicación denegado: actívalo en el navegador.', 2: 'Sin señal de ubicación.', 3: 'Se agotó el tiempo al obtener la ubicación.' }[e.code] || 'No se pudo obtener la ubicación.';
    msg(t); setTriggerValue('error', t);
  };
  if (!('geolocation' in navigator) || !window.isSecureContext) {
    msg('La ubicación requiere HTTPS (o localhost) y un navegador compatible.');
    return;
  }
  $('once').onclick = () => { msg('Buscando ubicación…'); last = null; navigator.geolocation.getCurrentPosition(send, fail, opts); };
  $('live').onclick = () => {
    const live = $('live');
    if (window.__hzGeoWatch != null) {
      navigator.geolocation.clearWatch(window.__hzGeoWatch); window.__hzGeoWatch = null;
      live.setAttribute('aria-pressed', 'false'); msg('Seguimiento detenido.'); return;
    }
    last = null; msg('Siguiendo tu ubicación…'); live.setAttribute('aria-pressed', 'true');
    window.__hzGeoWatch = navigator.geolocation.watchPosition(send, fail, opts);
  };
  if (window.__hzGeoWatch != null) { $('live').setAttribute('aria-pressed', 'true'); msg('Siguiendo tu ubicación…'); }
}
"""

_component = st.components.v2.component(
    "hazmat_geolocate", html=_HTML, css=_CSS, js=_JS
)


def parse_position(value) -> tuple[float, float, float] | None:
    """Valida lo que envía el navegador → (lat, lon, precisión_m) o None."""
    try:
        lat, lon = float(value["lat"]), float(value["lon"])
        acc = float(value.get("accuracy") or 0)
    except (TypeError, KeyError, ValueError):
        return None
    if (
        not (-90 <= lat <= 90 and -180 <= lon <= 180)
        or not math.isfinite(acc)
        or acc < 0
    ):
        return None
    return lat, lon, acc


def geolocate(key: str = "geo") -> tuple[float, float, float] | None:
    """Muestra los botones y devuelve la última posición nueva (o None si no hay)."""
    result = _component(
        key=key, on_position_change=lambda: None, on_error_change=lambda: None
    )
    return parse_position(getattr(result, "position", None))
