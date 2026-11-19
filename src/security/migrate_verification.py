"""Migración de cuentas existentes a la verificación de correo (v5.3.0).

    python -m src.security.migrate_verification --dry-run        # solo informa (por defecto)
    python -m src.security.migrate_verification --apply          # marca email_verified: False
    python -m src.security.migrate_verification --verify-user admin   # verificación manual

- Las cuentas con correo verificarán con un código en su siguiente inicio de sesión.
- Las cuentas sin correo deberán ingresar uno al iniciar sesión y luego verificarlo.
- Las migradas NO reciben `pending_expires_at`: nunca las borra el TTL ni `purge-unverified`.
- Para no dejar a ningún admin bloqueado de forma permanente: `--apply` se niega si SMTP no está
  configurado y `--verify-user` permite al operador del servidor verificar una cuenta a mano.
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime

from src.config.features import features
from src.observability.store import security_event
from src.security.accounts import _users

LEGACY = {"email_verified": {"$exists": False}}


def summary() -> dict[str, int]:
    col = _users()
    with_email = {**LEGACY, "email": {"$type": "string"}}
    return {
        "total_sin_migrar": col.count_documents(LEGACY),
        "con_correo": col.count_documents(with_email),
        "sin_correo": col.count_documents(LEGACY) - col.count_documents(with_email),
        "admins": col.count_documents({**LEGACY, "role": "admin"}),
    }


def apply() -> int:
    if not features.mail_enabled:
        raise RuntimeError(
            "SMTP no configurado: nadie podría recibir su código (incluidos los admins). "
            "Configura SMTP_USER/SMTP_PASSWORD antes de aplicar."
        )
    res = _users().update_many(LEGACY, {"$set": {"email_verified": False}})
    security_event(
        "verification_migration",
        detail=f"{res.modified_count} cuentas",
        severity="medium",
    )
    return res.modified_count


def verify_user(username: str) -> bool:
    res = _users().update_one(
        {"_id": username},
        {
            "$set": {"email_verified": True, "email_verified_at": datetime.now(UTC)},
            "$unset": {"pending_expires_at": ""},
        },
    )
    if res.matched_count:
        security_event("email_verified_manual", user_id=username, severity="medium")
    return bool(res.matched_count)


def main() -> int:
    parser = argparse.ArgumentParser(description="Migración a verificación de correo")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", action="store_true", help="Solo informar (defecto)")
    group.add_argument("--apply", action="store_true", help="Aplicar la migración")
    group.add_argument("--verify-user", metavar="USUARIO", help="Verificar a mano")
    args = parser.parse_args()
    if args.verify_user:
        ok = verify_user(args.verify_user)
        print("Cuenta verificada." if ok else "No existe esa cuenta.")
        return 0 if ok else 1
    for key, value in summary().items():
        print(f"{key}: {value}")
    if not args.apply:
        print("Simulación: no se modificó nada. Usa --apply para aplicar.")
        return 0
    try:
        print(f"Cuentas marcadas para verificar: {apply()}")
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
