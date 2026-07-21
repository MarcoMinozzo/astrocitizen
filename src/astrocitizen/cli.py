"""CLI do AstroCitizen (S1: init-db, site, equipment, program)."""

from __future__ import annotations

import argparse
from pathlib import Path

from astrocitizen import __version__
from astrocitizen.adapters.fs import LocalArtifactStore
from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.inventory.models import Equipment, Site
from astrocitizen.programs.models import Program
from astrocitizen.programs.seed import seed_program_templates
from astrocitizen.shared import CONTEXT_MODULES
from astrocitizen.shared.ids import new_id
from astrocitizen.shared.paths import default_artifacts_root, default_db_path
from astrocitizen.workspace.models import Workspace

DEFAULT_WORKSPACE_NAME = "default"


def _open_archive(db: Path) -> SqliteArchive:
    archive = SqliteArchive(db)
    archive.migrate()
    return archive


def _ensure_default_workspace(archive: SqliteArchive) -> Workspace:
    workspaces = archive.list_workspaces()
    if workspaces:
        return workspaces[0]
    ws = Workspace(id=new_id(), name=DEFAULT_WORKSPACE_NAME)
    return archive.upsert_workspace(ws)


def _cmd_init_db(args: argparse.Namespace) -> int:
    db = Path(args.db)
    artifacts = Path(args.artifacts)
    archive = _open_archive(db)
    ws = _ensure_default_workspace(archive)
    n = seed_program_templates(archive)
    LocalArtifactStore(artifacts)  # cria root
    print(f"db={db}")
    print(f"artifacts={artifacts.resolve()}")
    print(f"schema=ok workspace={ws.id} name={ws.name}")
    print(f"templates_seeded={n}")
    archive.close()
    return 0


def _cmd_site_add(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    site = Site(
        id=new_id(),
        workspace_id=ws.id,
        name=args.name,
        latitude_deg=args.lat,
        longitude_deg=args.lon,
        elevation_m=args.elev,
        timezone=args.tz,
        is_default=args.default,
    )
    archive.upsert_site(site)
    print(f"{site.id}\t{site.name}\t{site.latitude_deg},{site.longitude_deg}")
    archive.close()
    return 0


def _cmd_site_list(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    for s in archive.list_sites(ws.id):
        flag = "*" if s.is_default else " "
        print(f"{flag}\t{s.id}\t{s.name}\t{s.latitude_deg},{s.longitude_deg}\t{s.timezone}")
    archive.close()
    return 0


def _cmd_equipment_add(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    eq = Equipment(
        id=new_id(),
        workspace_id=ws.id,
        type=args.type,
        name=args.name,
        backend=args.backend,
    )
    archive.upsert_equipment(eq)
    print(f"{eq.id}\t{eq.type}\t{eq.name}\t{eq.backend or '-'}")
    archive.close()
    return 0


def _cmd_equipment_list(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    for eq in archive.list_equipment(ws.id):
        print(f"{eq.id}\t{eq.type}\t{eq.name}\t{eq.backend or '-'}")
    archive.close()
    return 0


def _cmd_program_templates(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    if not archive.list_program_templates():
        seed_program_templates(archive)
    for t in archive.list_program_templates(class_=args.class_):
        nets = ",".join(t.default_networks) if t.default_networks else "-"
        print(f"{t.id}\t{t.priority}\t{t.name}\t{nets}")
    archive.close()
    return 0


def _cmd_program_create(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    if not archive.list_program_templates():
        seed_program_templates(archive)
    tmpl = archive.get_program_template(args.template)
    if tmpl is None:
        print(f"template nao encontrado: {args.template}")
        archive.close()
        return 1
    name = args.name or tmpl.name
    program = Program(
        id=new_id(),
        workspace_id=ws.id,
        template_id=tmpl.id,
        name=name,
        state="draft",
        export_networks=list(tmpl.default_networks),
        minimum_product=tmpl.minimum_product,
    )
    archive.upsert_program(program)
    print(f"{program.id}\t{program.template_id}\t{program.state}\t{program.name}")
    archive.close()
    return 0


def _cmd_program_list(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    for p in archive.list_programs(ws.id, state=args.state):
        print(f"{p.id}\t{p.template_id}\t{p.state}\t{p.name}")
    archive.close()
    return 0


def _add_db_arg(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--db",
        default=str(default_db_path()),
        help="Caminho do SQLite (default: ~/.astrocitizen/astrocitizen.sqlite3)",
    )


def build_parser() -> argparse.ArgumentParser:
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

    p_init = sub.add_parser("init-db", help="Criar BD SQLite, workspace e seed PO-*")
    _add_db_arg(p_init)
    p_init.add_argument(
        "--artifacts",
        default=str(default_artifacts_root()),
        help="Root do ArtifactStore local",
    )
    p_init.set_defaults(func=_cmd_init_db)

    p_site = sub.add_parser("site", help="Gerir sites observacionais")
    site_sub = p_site.add_subparsers(dest="site_cmd", required=True)
    p_site_add = site_sub.add_parser("add", help="Adicionar site")
    _add_db_arg(p_site_add)
    p_site_add.add_argument("--name", required=True)
    p_site_add.add_argument("--lat", type=float, required=True)
    p_site_add.add_argument("--lon", type=float, required=True)
    p_site_add.add_argument("--elev", type=float, default=0.0)
    p_site_add.add_argument("--tz", default="UTC")
    p_site_add.add_argument("--default", action="store_true")
    p_site_add.set_defaults(func=_cmd_site_add)
    p_site_list = site_sub.add_parser("list", help="Listar sites")
    _add_db_arg(p_site_list)
    p_site_list.set_defaults(func=_cmd_site_list)

    p_eq = sub.add_parser("equipment", help="Gerir inventario de equipamento")
    eq_sub = p_eq.add_subparsers(dest="eq_cmd", required=True)
    p_eq_add = eq_sub.add_parser("add", help="Adicionar equipamento")
    _add_db_arg(p_eq_add)
    p_eq_add.add_argument("--type", required=True, help="camera|mount|focuser|filter_wheel|...")
    p_eq_add.add_argument("--name", required=True)
    p_eq_add.add_argument("--backend", default=None)
    p_eq_add.set_defaults(func=_cmd_equipment_add)
    p_eq_list = eq_sub.add_parser("list", help="Listar equipamento")
    _add_db_arg(p_eq_list)
    p_eq_list.set_defaults(func=_cmd_equipment_list)

    p_prog = sub.add_parser("program", help="Gerir programas observacionais")
    prog_sub = p_prog.add_subparsers(dest="prog_cmd", required=True)
    p_tmpl = prog_sub.add_parser("templates", help="Listar templates PO-*")
    _add_db_arg(p_tmpl)
    p_tmpl.add_argument("--class", dest="class_", default=None, help="Filtrar por classe A-K")
    p_tmpl.set_defaults(func=_cmd_program_templates)
    p_create = prog_sub.add_parser("create", help="Criar programa a partir de template")
    _add_db_arg(p_create)
    p_create.add_argument("--template", required=True, help="ex.: PO-A01")
    p_create.add_argument("--name", default=None)
    p_create.set_defaults(func=_cmd_program_create)
    p_plist = prog_sub.add_parser("list", help="Listar programas")
    _add_db_arg(p_plist)
    p_plist.add_argument("--state", default=None)
    p_plist.set_defaults(func=_cmd_program_list)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
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

    func = getattr(args, "func", None)
    if func is None:
        parser.print_help()
        return 1
    return int(func(args))


if __name__ == "__main__":
    raise SystemExit(main())
