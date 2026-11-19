"""Explicación del panel de observabilidad: qué es, para qué sirve, cómo funciona y qué pide la rúbrica."""

from __future__ import annotations

import streamlit as st

from src.config.features import features

EVENT_NAMES = {
    "login_failed": "Inicio de sesión fallido",
    "login_locked": "Intento sobre cuenta bloqueada",
    "account_locked": "Cuenta bloqueada",
    "signup": "Cuenta creada",
    "signup_failed": "Registro con error",
    "signup_rolled_back": "Registro anulado",
    "signup_blocked": "Registro bloqueado (sin correo)",
    "signup_throttled": "Límite de registros",
    "otp_sent": "Código enviado",
    "otp_failed": "Código incorrecto",
    "otp_resend": "Código reenviado",
    "otp_send_failed": "Código no enviado",
    "email_verified": "Correo verificado",
    "privacy_accepted": "Aviso de privacidad aceptado",
    "reset_requested": "Recuperación solicitada",
    "reset_failed": "Recuperación fallida",
    "password_reset": "Contraseña cambiada",
    "throttled": "Límite anti-abuso",
    "rate_limit": "Límite de consultas",
    "auth_ui_error": "Error en pantalla de acceso",
    "blocked_injection": "Bloqueo: manipulación",
    "blocked_harmful": "Bloqueo: intención de daño",
    "blocked_out_of_domain": "Bloqueo: fuera de dominio",
    "blocked_secrets": "Bloqueo: credenciales",
}

_FLOW = """
| 1. Consulta | 2. Telemetría | 3. Almacenamiento | 4. Este panel | 5. Avisos |
|---|---|---|---|---|
| Alguien pregunta en el chat | El agente mide tiempos por etapa, tokens, errores, bloqueos y citas | MongoDB (`agent_runs`, `security_events`), **seudonimizado** y con borrado a los 180 días | Lee esos datos en vivo (se actualiza cada 30 s) | Cada 30 min se revisan los umbrales y se envía un correo al admin; cada noche se corre la evaluación |
"""


def render_intro() -> None:
    with st.expander(
        "¿Qué es este panel y para qué sirve?", icon=":material/lightbulb:"
    ):
        st.markdown(
            "**Qué es.** La *observabilidad* es medir en vivo cómo se comporta el asistente cuando "
            "lo usan personas reales: qué tan rápido responde, cuántas veces falla, cuánto cuesta, "
            "si sus citas son verdaderas y si alguien intenta abusar de él. No muestra el texto de las "
            "consultas ni quién las hizo: los usuarios están seudonimizados."
        )
        st.markdown(
            "**Para qué sirve.** En una emergencia una respuesta lenta o inventada es peligrosa. Este "
            "panel permite **detectar** problemas (modelo saturado, cuota agotada, base caída), "
            "**verificar** la calidad (citas comprobadas, feedback 👍/👎, evaluación nocturna) y "
            "**mejorar** el sistema (cada 👎 se puede convertir en un caso de prueba)."
        )
        st.markdown("**Cómo funciona.**")
        st.markdown(_FLOW)
        st.markdown(
            f"**Cómo leer los colores.** Verde = dentro de lo esperado · Ámbar = revisar · Rojo = "
            f"actuar. Umbrales: latencia p95 {features.ALERT_P95_S:g} s, errores "
            f"{features.ALERT_ERROR_RATE:.0%}, bloqueos {features.ALERT_BLOCKED_RATE:.0%} (variables "
            "`ALERT_*` del `.env`)."
        )
        st.markdown(
            "**Rúbrica EV3.** Cubre el registro de métricas por ejecución (IE1), el análisis de "
            "latencia, errores y uso de recursos (IE2), y la calidad y seguridad de las respuestas "
            "con evaluación continua (IE3)."
        )


TABS_HELP = {
    "usage": "Rapidez, errores, calidad y costo de las respuestas a usuarios reales.",
    "security": "Ataques y abusos detenidos, datos personales ocultados y auditoría de cuentas.",
    "offline": "Resultados de la evaluación automática con preguntas de referencia (cada noche).",
    "improve": "Respuestas marcadas con 👎 que un admin puede convertir en casos de prueba.",
    "log": "Detalle de cada ejecución para investigar un problema puntual.",
}
