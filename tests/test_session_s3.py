"""Testes S3 — hardware sim, sessao, FITS."""

from __future__ import annotations

from pathlib import Path

from astropy.io import fits

from astrocitizen.adapters.fs import LocalArtifactStore
from astrocitizen.adapters.hardware import create_camera, create_focuser, create_mount
from astrocitizen.adapters.meteo import ManualMeteo
from astrocitizen.adapters.sky import AstropyEphemeris
from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.adapters.sqlite.schema import SCHEMA_VERSION
from astrocitizen.inventory.models import Equipment, InstrumentConfig, Site
from astrocitizen.observatory import CaptureObservation, ExecuteSession, mark_block_failed
from astrocitizen.planning import GenerateDailyPlan, Target
from astrocitizen.programs.models import Program
from astrocitizen.programs.seed import seed_program_templates
from astrocitizen.shared.errors import DomainError
from astrocitizen.shared.ids import new_id
from astrocitizen.workspace.models import Workspace


def _world(tmp_path: Path):
    archive = SqliteArchive(tmp_path / "s3.sqlite3")
    assert archive.migrate() == SCHEMA_VERSION == 3
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    seed_program_templates(archive)
    site = archive.upsert_site(
        Site(
            id=new_id(),
            workspace_id=ws.id,
            name="Casa",
            latitude_deg=-29.68,
            longitude_deg=-51.13,
            elevation_m=30.0,
            min_altitude_deg=10.0,
            is_default=True,
        )
    )
    cam = archive.upsert_equipment(
        Equipment(id=new_id(), workspace_id=ws.id, type="camera", name="SimCam", backend="sim")
    )
    mount = archive.upsert_equipment(
        Equipment(id=new_id(), workspace_id=ws.id, type="mount", name="SimMount", backend="sim")
    )
    cfg = archive.upsert_instrument_config(
        InstrumentConfig(
            id=new_id(),
            workspace_id=ws.id,
            name="Setup",
            items={"camera": cam.id, "mount": mount.id},
        )
    )
    prog = archive.upsert_program(
        Program(
            id=new_id(),
            workspace_id=ws.id,
            template_id="PO-A01",
            name="Vars",
            state="active",
            priority=1,
            default_instrument_config_id=cfg.id,
        )
    )
    target = archive.upsert_target(
        Target(
            id=new_id(),
            workspace_id=ws.id,
            designation="StarA",
            ra_deg=180.0,
            dec_deg=-30.0,
        )
    )
    archive.link_program_target(prog.id, target.id)
    plan = GenerateDailyPlan(archive, AstropyEphemeris(), ManualMeteo()).execute(
        workspace_id=ws.id,
        site_id=site.id,
        night_date="2026-07-15",
    )
    return archive, ws, plan


def test_simulator_camera_fits(tmp_path: Path) -> None:
    cam = create_camera("sim", width=32, height=32)
    cam.connect()
    meta = cam.expose(exptime_s=0.5)
    assert meta["EXPTIME"] == 0.5
    path = tmp_path / "frame.fits"
    cam.save_fits(path, headers={"OBJECT": "TEST"})
    with fits.open(path) as hdul:
        assert hdul[0].data.shape == (32, 32)
        assert hdul[0].header["OBJECT"] == "TEST"
    create_mount("sim").connect()
    create_focuser("sim").connect()


def test_session_capture_flow(tmp_path: Path) -> None:
    archive, ws, plan = _world(tmp_path)
    blocks = archive.list_observation_blocks(plan.id)
    assert blocks
    # Prefer a block that can run; force status agendado for capture test
    block = blocks[0]
    block.status = "agendado"
    archive.update_observation_block(block)

    session = ExecuteSession(archive).start(workspace_id=ws.id, plan_id=plan.id)
    assert session.plan_snapshot["schema"] == 1
    assert session.daily_plan_version == plan.version
    refreshed = archive.get_daily_plan(plan.id)
    assert refreshed is not None and refreshed.state == "in_execution"

    store = LocalArtifactStore(tmp_path / "artifacts")
    cam = create_camera("sim", width=16, height=16)
    obs = CaptureObservation(archive, cam, store).execute(
        session_id=session.id,
        block_id=block.id,
        exptime_s=1.0,
    )
    assert obs.simulated is True
    assert obs.session_id == session.id
    assert obs.headers_summary.get("CAMBACK") == "sim"

    done = archive.get_observation_block(block.id)
    assert done is not None and done.status == "concluido"

    rows = archive.list_observations(ws.id, include_simulated=True)
    assert any(r["id"] == str(obs.id) for r in rows)

    ExecuteSession(archive).end(session.id)
    ended = archive.get_session(session.id)
    assert ended is not None and ended.state == "ended"
    archive.close()


def test_instrument_failure_marks_block(tmp_path: Path) -> None:
    archive, ws, plan = _world(tmp_path)
    block = archive.list_observation_blocks(plan.id)[0]
    session = ExecuteSession(archive).start(workspace_id=ws.id, plan_id=plan.id)
    mark_block_failed(
        archive,
        session_id=session.id,
        block_id=block.id,
        reason="camera timeout",
    )
    failed = archive.get_observation_block(block.id)
    assert failed is not None and failed.status == "falhou"
    archive.close()


def test_capture_without_connect_fails_block(tmp_path: Path) -> None:
    archive, ws, plan = _world(tmp_path)
    block = archive.list_observation_blocks(plan.id)[0]
    block.status = "agendado"
    archive.update_observation_block(block)
    session = ExecuteSession(archive).start(workspace_id=ws.id, plan_id=plan.id)
    store = LocalArtifactStore(tmp_path / "artifacts")
    cam = create_camera("sim")
    # expose without connect -> DomainError, block falhou
    # CaptureObservation.connects automatically; force disconnect mid-way by
    # replacing expose
    original = cam.expose

    def boom(**kwargs):
        raise DomainError("hardware fault", rule_id="RN-092")

    cam.expose = boom  # type: ignore[method-assign]
    try:
        CaptureObservation(archive, cam, store).execute(
            session_id=session.id, block_id=block.id
        )
        raise AssertionError("expected DomainError")
    except DomainError:
        pass
    failed = archive.get_observation_block(block.id)
    assert failed is not None and failed.status == "falhou"
    cam.expose = original  # type: ignore[method-assign]
    archive.close()


def test_udrv_stub_raises() -> None:
    cam = create_camera("udrv")
    try:
        cam.connect()
        raise AssertionError("expected")
    except DomainError as exc:
        assert "sbig-suite" in str(exc) or "AC-042" in str(exc.rule_id or "")
