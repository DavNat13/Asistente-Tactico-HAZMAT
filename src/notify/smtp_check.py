"""Diagnóstico del correo real (Gmail SMTP).

    python -m src.notify.smtp_check                       # TLS + inicio de sesión, sin enviar nada
    python -m src.notify.smtp_check --send-to tu@correo   # además envía un correo de prueba

Nunca muestra la contraseña. Código de salida 1 si algo falla (útil en CI o al desplegar).
"""

from __future__ import annotations

import argparse
import smtplib
import ssl
import sys

from src.config.features import features
from src.notify.mailer import send
from src.notify.templates import layout, paragraph

HINTS = {
    "SMTPAuthenticationError": (
        "Usuario o contraseña rechazados. En Gmail usa una «contraseña de aplicación» de 16 "
        "caracteres (requiere verificación en 2 pasos), no tu contraseña normal."
    ),
    "SMTPConnectError": "No se pudo conectar. Revisa SMTP_HOST/SMTP_PORT (Gmail: smtp.gmail.com:465).",
    "TimeoutError": "Tiempo de espera agotado: firewall, red o puerto bloqueado.",
    "SSLError": "Fallo de TLS: el puerto 465 requiere SSL implícito.",
    "gaierror": "No se resuelve el servidor: revisa SMTP_HOST o la conexión a internet.",
}


def check_login() -> tuple[bool, str]:
    if features.mail_problem:
        return False, f"Configuración inválida: {features.mail_problem}"
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(
            features.SMTP_HOST, features.SMTP_PORT, context=context, timeout=20
        ) as smtp:
            smtp.login(features.SMTP_USER, features.SMTP_PASSWORD)
    except (smtplib.SMTPException, OSError) as e:
        name = type(e).__name__
        return False, f"{name}: {HINTS.get(name, 'error inesperado del servidor SMTP')}"
    return (
        True,
        f"Login OK en {features.SMTP_HOST}:{features.SMTP_PORT} como {features.SMTP_USER}",
    )


def send_test(to: str) -> tuple[bool, str]:
    body = paragraph("Este es un correo de prueba del Asistente HAZMAT.") + paragraph(
        "Si lo recibes, el envío de códigos de verificación funciona."
    )
    ok = send(
        [to],
        "Prueba de correo · Asistente HAZMAT",
        layout("Prueba de correo", body),
        "Correo de prueba del Asistente HAZMAT.",
        kind="smtp_test",
    )
    if ok:
        return (
            True,
            "El servidor aceptó el correo. Revisa la bandeja de entrada y spam.",
        )
    return (
        False,
        "El servidor no aceptó el correo (ver email_log y el log del servidor).",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Diagnóstico SMTP")
    parser.add_argument("--send-to", metavar="CORREO", help="Envía un correo de prueba")
    args = parser.parse_args(argv)
    ok, message = check_login()
    print(("✔ " if ok else "✖ ") + message)
    if ok and args.send_to:
        ok, message = send_test(args.send_to)
        print(("✔ " if ok else "✖ ") + message)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
