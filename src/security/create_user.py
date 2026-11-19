"""Crea o actualiza un usuario del asistente.

Uso:
    python -m src.security.create_user --username jperez --role operador --name "Juan Pérez"
    python -m src.security.create_user --username admin --role admin --email admin@dominio.cl

Vía de entrada garantizada: las cuentas creadas aquí quedan con el correo verificado
(`email_verified: True`), así que entran aunque el SMTP no funcione.

La contraseña se pide de forma interactiva (no queda en el historial de la terminal).
"""

from __future__ import annotations

import argparse
import getpass
import sys

from src.security.auth import ROLES, create_user


def main() -> None:
    parser = argparse.ArgumentParser(description="Crear usuario del Asistente HAZMAT")
    parser.add_argument("--username", required=True)
    parser.add_argument("--role", choices=ROLES, default="operador")
    parser.add_argument("--name", default="")
    parser.add_argument("--email", default=None, help="Correo (opcional)")
    args = parser.parse_args()

    password = getpass.getpass("Contraseña (mín. 10 caracteres): ")
    if password != getpass.getpass("Repite la contraseña: "):
        sys.exit("Las contraseñas no coinciden.")
    try:
        user = create_user(
            args.username,
            password,
            args.role,
            args.name,
            overwrite=True,
            email=args.email,
            extra={"email_verified": True},
        )
    except ValueError as e:
        sys.exit(f"Error: {e}")
    print(f"Usuario '{user['_id']}' ({user['role']}) creado/actualizado.")


if __name__ == "__main__":
    main()
