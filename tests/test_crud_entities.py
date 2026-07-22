"""CRUD dominio Site/Programa/Alvo (archive + soft delete)."""

from __future__ import annotations

from pathlib import Path

from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.inventory.models import Site
from astrocitizen.planning.models import Target
from astrocitizen.programs.models import Program
from astrocitizen.programs.seed import seed_program_templates
from astrocitizen.shared.ids import new_id
from astrocitizen.workspace.models import Workspace


def test_site_program_target_crud_roundtrip(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "c.sqlite3")
    archive.migrate()
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    site = archive.upsert_site(
        Site(
            id=new_id(),
            workspace_id=ws.id,
            name="Obs1",
            latitude_deg=-23.5,
            longitude_deg=-46.6,
            is_default=True,
        )
    )
    assert archive.get_site(site.id) is not None
    seed_program_templates(archive)
    tpl = archive.list_program_templates()[0]
    prog = archive.upsert_program(
        Program(
            id=new_id(),
            workspace_id=ws.id,
            template_id=tpl.id,
            name="Prog1",
            state="active",
        )
    )
    target = archive.upsert_target(
        Target(
            id=new_id(),
            workspace_id=ws.id,
            designation="Vega",
            ra_deg=279.23,
            dec_deg=38.78,
        )
    )
    archive.link_program_target(prog.id, target.id)
    linked = archive.list_program_targets(prog.id)
    assert len(linked) == 1
    assert linked[0][0].designation == "Vega"

    archive.soft_delete_target(target.id)
    assert archive.get_target(target.id) is None
    assert archive.list_targets(ws.id) == []

    archive.soft_delete_program(prog.id)
    assert archive.get_program(prog.id) is None
    archive.soft_delete_site(site.id)
    assert archive.get_site(site.id) is None
    archive.close()


def test_entities_builders_importable() -> None:
    from astrocitizen.desktop.entities import (
        build_programs_page,
        build_sites_page,
        build_targets_page,
    )

    assert callable(build_sites_page)
    assert callable(build_programs_page)
    assert callable(build_targets_page)
