"""Equipamento + InstrumentConfig + atribuicao a programa."""

from __future__ import annotations

from pathlib import Path

from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.inventory.models import Equipment, InstrumentConfig
from astrocitizen.programs.models import Program
from astrocitizen.programs.seed import seed_program_templates
from astrocitizen.shared.ids import new_id
from astrocitizen.workspace.models import Workspace


def test_equipment_config_assign_program(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "e.sqlite3")
    archive.migrate()
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    cam = archive.upsert_equipment(
        Equipment(
            id=new_id(),
            workspace_id=ws.id,
            type="camera",
            name="SimCam",
            backend="sim",
        )
    )
    mount = archive.upsert_equipment(
        Equipment(
            id=new_id(),
            workspace_id=ws.id,
            type="mount",
            name="SimMount",
            backend="sim",
        )
    )
    cfg = archive.upsert_instrument_config(
        InstrumentConfig(
            id=new_id(),
            workspace_id=ws.id,
            name="Setup A",
            notes="wizard",
            items={"camera": cam.id, "mount": mount.id},
        )
    )
    loaded = archive.get_instrument_config(cfg.id)
    assert loaded is not None
    assert loaded.items["camera"] == cam.id
    assert loaded.items["mount"] == mount.id

    seed_program_templates(archive)
    prog = archive.upsert_program(
        Program(
            id=new_id(),
            workspace_id=ws.id,
            template_id="PO-A01",
            name="Vars",
            state="active",
            default_instrument_config_id=cfg.id,
        )
    )
    assert prog.default_instrument_config_id == cfg.id
    again = archive.get_program(prog.id)
    assert again is not None and again.default_instrument_config_id == cfg.id

    archive.soft_delete_equipment(cam.id)
    assert archive.get_equipment(cam.id) is None
    archive.close()


def test_equipment_page_builder() -> None:
    from astrocitizen.desktop.equipment import build_equipment_page

    assert callable(build_equipment_page)
