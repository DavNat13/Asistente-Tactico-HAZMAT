"""Crea o actualiza un usuario del asistente.

Uso:
    python -m src.security.create_user --username jperez --role operador --name "Juan Pérez"
    python -m src.security.create_user --username admin --role admin

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
    args = parser.parse_args()

    password = getpass.getpass("Contraseña (mín. 10 caracteres): ")
    if password != getpass.getpass("Repite la contraseña: "):
        sys.exit("Las contraseñas no coinciden.")
    try:
        user = create_user(
            args.username, password, args.role, args.name, overwrite=True
        )
    except ValueError as e:
        sys.exit(f"Error: {e}")
    print(f"Usuario '{user['_id']}' ({user['role']}) creado/actualizado.")


if __name__ == "__main__":
    main()
