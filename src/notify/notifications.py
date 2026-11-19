"""Notificaciones por correo de alto nivel: cuenta, alertas, reporte semanal y ficha de incidente."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from src.config.features import features
from src.notify.mailer import EMAIL_LOG, send
from src.notify.templates import app_link, code_box, layout, paragraph, table
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


_CODE_COPY = {
    "signup": ("Verifica tu correo", "Usa este código para activar tu cuenta.", 15),
    "reset": (
        "Restablece tu contraseña",
        "Usa este código para crear una nueva contraseña.",
        10,
    ),
}


def send_code(user: dict, code: str, purpose: str) -> bool:
    """Envío SÍNCRONO del código: el resultado decide si el registro se completa."""
    title, intro, minutes = _CODE_COPY[purpose]
    body = (
        paragraph(f"Hola {user.get('name') or user['_id']}. {intro}")
        + code_box(code)
        + paragraph(f"Vence en {minutes} minutos y sirve una sola vez.")
        + paragraph(
            "Si no fuiste tú, ignora este mensaje. Nunca te pediremos este código."
        )
    )
    text = (
        f"{intro}\nCódigo: {code}\nVence en {minutes} minutos. "
        "Si no fuiste tú, ignora este correo."
    )
    subject = f"{title} · Asistente HAZMAT"
    return send(
        [user["email"]], subject, layout(title, body), text, kind=f"otp_{purpose}"
    )


def notify_password_changed(user: dict) -> None:
    body = paragraph(
        "La contraseña de tu cuenta del Asistente HAZMAT fue cambiada."
    ) + paragraph(
        "Si no fuiste tú, contacta de inmediato al administrador del sistema."
    )
    run_async(
        lambda: send(
            [user["email"]],
            "Aviso de seguridad: tu contraseña fue cambiada",
            layout("Tu contraseña fue cambiada", body),
            "Tu contraseña fue cambiada. Si no fuiste tú, contacta al administrador.",
            kind="password_changed",
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
