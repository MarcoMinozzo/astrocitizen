"""Testes S1 — SQLite ArchivePort, seed PO-*, ArtifactStore, soft-delete."""

from __future__ import annotations

from pathlib import Path

from astrocitizen.adapters.fs import LocalArtifactStore
from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.adapters.sqlite.schema import SCHEMA_VERSION
from astrocitizen.inventory.models import Equipment, InstrumentConfig, Site
from astrocitizen.programs.models import Program
from astrocitizen.programs.seed import seed_program_templates
from astrocitizen.shared.ids import new_id
from astrocitizen.shared.timeutil import utc_now_iso
from astrocitizen.workspace.models import Workspace


def _archive(tmp_path: Path) -> SqliteArchive:
    db = tmp_path / "test.sqlite3"
    archive = SqliteArchive(db)
    assert archive.migrate() == SCHEMA_VERSION
    assert archive.healthcheck()
    return archive


def test_migrate_idempotent(tmp_path: Path) -> None:
    archive = _archive(tmp_path)
    assert archive.migrate() == SCHEMA_VERSION
    archive.close()


def test_site_equipment_program_flow(tmp_path: Path) -> None:
    archive = _archive(tmp_path)
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    n = seed_program_templates(archive)
    assert n >= 40
    assert archive.get_program_template("PO-A01") is not None

    site = archive.upsert_site(
        Site(
            id=new_id(),
            workspace_id=ws.id,
            name="Observatorio Casa",
            latitude_deg=-29.68,
            longitude_deg=-51.13,
            elevation_m=30.0,
            timezone="America/Sao_Paulo",
            is_default=True,
        )
    )
    assert archive.list_sites(ws.id)[0].id == site.id

    cam = archive.upsert_equipment(
        Equipment(
            id=new_id(),
            workspace_id=ws.id,
            type="camera",
            name="SBIG ST-7",
            backend="udrv",
        )
    )
    mount = archive.upsert_equipment(
        Equipment(
            id=new_id(),
            workspace_id=ws.id,
            type="mount",
            name="EQ6",
            backend="alpaca",
        )
    )
    cfg = archive.upsert_instrument_config(
        InstrumentConfig(
            id=new_id(),
            workspace_id=ws.id,
            name="Setup principal",
            items={"camera": cam.id, "mount": mount.id},
        )
    )
    loaded = archive.get_instrument_config(cfg.id)
    assert loaded is not None
    assert loaded.items["camera"] == cam.id

    tmpl = archive.get_program_template("PO-A01")
    assert tmpl is not None
    prog = archive.upsert_program(
        Program(
            id=new_id(),
            workspace_id=ws.id,
            template_id=tmpl.id,
            name="Variaveis 2026",
            state="active",
            export_networks=list(tmpl.default_networks),
            default_instrument_config_id=cfg.id,
        )
    )
    assert archive.list_programs(ws.id, state="active")[0].id == prog.id
    archive.close()


def test_soft_delete_and_audit(tmp_path: Path) -> None:
    archive = _archive(tmp_path)
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    site = archive.upsert_site(
        Site(
            id=new_id(),
            workspace_id=ws.id,
            name="Temp",
            latitude_deg=0.0,
            longitude_deg=0.0,
        )
    )
    archive.soft_delete_site(site.id)
    assert archive.get_site(site.id) is None
    assert archive.list_sites(ws.id) == []
    audit = archive.list_audit(ws.id)
    assert any(a["action"] == "soft_delete" and a["entity_type"] == "sites" for a in audit)
    archive.close()


def test_simulated_observation_filter(tmp_path: Path) -> None:
    archive = _archive(tmp_path)
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    real_id = new_id()
    sim_id = new_id()
    archive.create_observation(
        observation_id=real_id,
        workspace_id=ws.id,
        observed_at_utc=utc_now_iso(),
        simulated=False,
    )
    archive.create_observation(
        observation_id=sim_id,
        workspace_id=ws.id,
        observed_at_utc=utc_now_iso(),
        simulated=True,
    )
    only_real = archive.list_observations(ws.id, include_simulated=False)
    assert len(only_real) == 1
    assert only_real[0]["id"] == str(real_id)
    both = archive.list_observations(ws.id, include_simulated=True)
    assert len(both) == 2
    archive.soft_delete_observation(real_id)
    remaining = archive.list_observations(ws.id, include_simulated=True)
    assert len(remaining) == 1
    assert remaining[0]["id"] == str(sim_id)
    archive.close()


def test_local_artifact_store(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    store = LocalArtifactStore(root)
    src = tmp_path / "frame.fits"
    src.write_bytes(b"SIMPLE  =                    T / mock")
    uri = store.put(src, key="raw/2026/frame.fits")
    assert store.exists(uri)
    assert store.resolve(uri).read_bytes().startswith(b"SIMPLE")
