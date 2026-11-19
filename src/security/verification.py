"""Verificación del correo con código de 6 dígitos.

Se usa en el registro, en cuentas migradas (`email_verified: False`) y en cuentas antiguas sin
correo (primero se pide el correo). Solo tras verificar se inicia sesión y se envía la bienvenida.
Reenvío: espera de 60 s por cuenta y máximo 5 envíos por hora por correo.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pymongo.errors import DuplicateKeyError

from src.observability.store import security_event
from src.security import otp, throttle
from src.security.accounts import _users, normalize_email, public

MAX_SENDS_PER_HOUR = 5


def _aware(dt: datetime) -> datetime:
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt


def expired(user: dict) -> bool:
    pending = user.get("pending_expires_at")
    return bool(pending and _aware(pending) <= datetime.now(UTC))


def send_code(user: dict, purpose: str = "signup") -> bool:
    """Emite y envía un código. ValueError si hay que esperar; False si el correo no salió."""
    left = otp.cooldown_left(user["_id"], purpose)
    if left:
        raise ValueError(f"Espera {left} s para pedir otro código")
    if not throttle.allow("otp_email", user["email"], MAX_SENDS_PER_HOUR):
        raise ValueError("Alcanzaste el máximo de códigos por hora. Intenta más tarde")
    code = otp.issue(user["_id"], purpose)
    from src.notify.notifications import send_code as mail_code

    ok = mail_code(user, code, purpose)
    if not ok:
        otp.invalidate(user["_id"], purpose)
    kind = "otp_sent" if ok else "otp_send_failed"
    security_event(kind, user_id=user["_id"], detail=purpose, severity="low")
    return ok


def _unverified(username: str) -> dict | None:
    user = _users().find_one({"_id": username})
    if not user or user.get("email_verified") is not False:
        return None
    if expired(user):  # el TTL de Mongo puede tardar ~1 min en borrarla
        cancel_pending(username)
        return None
    return user


def resend(username: str) -> bool:
    user = _unverified(username)
    if not user or not user.get("email"):
        return False
    security_event("otp_resend", user_id=username, detail="signup", severity="low")
    return send_code(user)


def ensure_code(username: str) -> bool:
    """Envía un código solo si la cuenta no tiene uno vigente (p. ej. cuentas migradas)."""
    user = _unverified(username)
    if not user or not user.get("email"):
        return False
    if otp.active(username, "signup"):
        return True
    return send_code(user)


def confirm(username: str, code: str) -> dict | None:
    """Valida el código y activa la cuenta. Devuelve la cuenta pública o None."""
    user = _unverified(username)
    if not user or not user.get("email") or not otp.verify(username, "signup", code):
        return None
    now = datetime.now(UTC)
    _users().update_one(
        {"_id": username},
        {
            "$set": {"email_verified": True, "email_verified_at": now},
            "$unset": {"pending_expires_at": ""},
        },
    )
    otp.invalidate(username)
    security_event(
        "email_verified", user_id=username, detail="correo verificado", severity="low"
    )
    account = public(user)
    if user.get("pending_expires_at"):  # cuenta nueva: la bienvenida llega recién ahora
        from src.notify.notifications import notify_welcome

        notify_welcome(account)
    return account


def set_email(username: str, email: str) -> bool:
    """Asocia (o corrige) el correo de una cuenta aún no verificada y le envía un código."""
    email = normalize_email(email)
    user = _unverified(username)
    if not user:
        return False
    try:
        _users().update_one({"_id": username}, {"$set": {"email": email}})
    except DuplicateKeyError:
        raise ValueError("No pudimos usar ese correo. Prueba con otro") from None
    otp.invalidate(username, "signup")
    return send_code({**user, "email": email})


def cancel_pending(username: str) -> bool:
    """Elimina una cuenta NUEVA no verificada ("Cambiar correo"). Nunca toca cuentas migradas."""
    res = _users().delete_one(
        {
            "_id": username,
            "email_verified": False,
            "pending_expires_at": {"$exists": True},
        }
    )
    otp.delete_for(username)
    return res.deleted_count == 1


def purge_unverified() -> int:
    """Borra cuentas nuevas no verificadas cuyo plazo venció (respaldo del índice TTL)."""
    query = {"email_verified": False, "pending_expires_at": {"$lt": datetime.now(UTC)}}
    ids = [u["_id"] for u in _users().find(query, {"_id": 1})]
    for uid in ids:
        otp.delete_for(uid)
    if ids:
        _users().delete_many({"_id": {"$in": ids}, **query})
    return len(ids)
