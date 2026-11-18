"""Envío de correo por SMTP (Gmail con contraseña de aplicación).

- Sin configuración (`SMTP_USER`/`SMTP_PASSWORD`) → no envía y lo registra (la app sigue funcionando).
- TLS implícito (SMTP_SSL, puerto 465) con verificación de certificado.
- Registro de envíos en `email_log` SIN contenido: tipo, destinatario seudonimizado y resultado.
"""

from __future__ import annotations

import logging
import smtplib
import ssl
from datetime import UTC, datetime
from email.message import EmailMessage

from src.config.features import features
from src.observability.store import get_db, pseudonymize

log = logging.getLogger("hazmat.mail")
EMAIL_LOG = "email_log"


def _log(
    kind: str, to: list[str], ok: bool, error: str = "", sender: str | None = None
) -> None:
    try:
        get_db()[EMAIL_LOG].insert_one(
            {
                "created_at": datetime.now(UTC),
                "kind": kind,
                "to": [pseudonymize(t) for t in to],
                "ok": ok,
                "error": error[:120],
                "sender": pseudonymize(sender),
            }
        )
    except Exception:  # noqa: BLE001
        log.warning("No se pudo registrar el envío de correo")


def build_message(
    to: list[str], subject: str, html: str, text: str, attachments: list | None = None
) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = f"Asistente HAZMAT <{features.MAIL_FROM}>"
    msg["To"] = ", ".join(to)
    msg["Subject"] = subject
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")
    for filename, data, mime in attachments or []:
        maintype, subtype = mime.split("/", 1)
        msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=filename)
    return msg


def send(
    to: list[str],
    subject: str,
    html: str,
    text: str,
    *,
    kind: str,
    attachments: list | None = None,
    sender: str | None = None,
) -> bool:
    """Envía el correo. Devuelve True si el servidor lo aceptó."""
    to = [t for t in (to or []) if t]
    if not to:
        return False
    if not features.mail_enabled:
        log.info("Correo '%s' omitido: SMTP no configurado", kind)
        _log(kind, to, False, "smtp_no_configurado", sender)
        return False
    msg = build_message(to, subject, html, text, attachments)
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(
            features.SMTP_HOST, features.SMTP_PORT, context=context, timeout=20
        ) as smtp:
            smtp.login(features.SMTP_USER, features.SMTP_PASSWORD)
            smtp.send_message(msg)
        _log(kind, to, True, sender=sender)
        return True
    except (smtplib.SMTPException, OSError) as e:
        log.warning("Fallo al enviar correo '%s': %s", kind, type(e).__name__)
        _log(kind, to, False, type(e).__name__, sender)
        return False
