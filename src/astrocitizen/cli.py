"""CLI minima do AstroCitizen (esqueleto S0)."""

from __future__ import annotations

import argparse

from astrocitizen import __version__
from astrocitizen.shared import CONTEXT_MODULES


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="astrocitizen",
        description="AstroCitizen - plataforma de astronomia observacional cidada",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"astrocitizen {__version__}",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("version", help="Mostrar versao do pacote")
    sub.add_parser("modules", help="Listar bounded contexts do skeleton")

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "version":
        print(__version__)
        return 0

    if args.command == "modules":
        for name in CONTEXT_MODULES:
            print(name)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
