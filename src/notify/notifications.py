"""Notificaciones por correo de alto nivel: cuenta, alertas, reporte semanal y ficha de incidente."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from src.config.features import features
from src.notify.mailer import EMAIL_LOG, send
from src.notify.templates import app_link, layout, paragraph, table
from src.observability.store import get_db, pseudonymize, run_async


def notify_welcome(user: dict) -> None:
    body = paragraph(
        f"Hola {user['name']}, tu cuenta fue creada correctamente."
    ) + paragraph(
        "Puedes consultar N° UN, materiales, distancias de aislamiento y planes de respuesta, "
        "siempre con la página de la GRE 2024 citada."
    )
    run_async(
        lambda: send(
            [user["email"]],
            "Bienvenido/a al Asistente HAZMAT",
            layout("Tu cuenta está lista", body, app_link()),
            f"Hola {user['name']}, tu cuenta del Asistente HAZMAT fue creada.",
            kind="welcome",
        )
    )


def notify_account_locked(user: dict) -> None:
    body = paragraph(
        "Detectamos varios intentos fallidos de inicio de sesión en tu cuenta, por lo que fue "
        "bloqueada temporalmente como medida de seguridad."
    ) + paragraph("Si no fuiste tú, avisa al administrador del sistema.")
    run_async(
        lambda: send(
            [user["email"]],
            "Aviso de seguridad: cuenta bloqueada temporalmente",
            layout("Cuenta bloqueada temporalmente", body),
            "Tu cuenta del Asistente HAZMAT fue bloqueada temporalmente por intentos fallidos.",
            kind="account_locked",
        )
    )


def notify_admins(
    subject: str, title: str, rows: list[tuple[str, str]], intro: str, kind: str
) -> bool:
    if not features.ADMIN_EMAILS:
        return False
    body = paragraph(intro) + table(rows)
    text = intro + "\n" + "\n".join(f"- {k}: {v}" for k, v in rows)
    return send(
        features.ADMIN_EMAILS, subject, layout(title, body, app_link()), text, kind=kind
    )


def mail_quota_left(username: str) -> int:
    """Envíos de ficha restantes en la última hora para este usuario (anti-abuso)."""
    since = datetime.now(UTC) - timedelta(hours=1)
    used = get_db()[EMAIL_LOG].count_documents(
        {
            "kind": "incident",
            "sender": pseudonymize(username),
            "created_at": {"$gte": since},
        }
    )
    return max(0, features.MAIL_MAX_PER_HOUR - used)


def send_incident_report(
    username: str, to: str, title: str, summary: str, pdf: bytes
) -> bool:
    body = paragraph(f"Se adjunta la ficha del incidente: {title}.") + paragraph(
        summary[:600]
    )
    ok = send(
        [to],
        f"Ficha de incidente HAZMAT — {title}",
        layout("Ficha de incidente", body),
        f"Ficha de incidente: {title}\n\n{summary[:600]}",
        kind="incident",
        attachments=[("ficha_incidente_hazmat.pdf", pdf, "application/pdf")],
        sender=username,
    )
    return ok
