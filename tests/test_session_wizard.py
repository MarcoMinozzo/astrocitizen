"""Wizard sessao IN-CAP (prepare + multi-frame)."""

from __future__ import annotations

from pathlib import Path

from astrocitizen.adapters.fs import LocalArtifactStore
from astrocitizen.adapters.hardware import create_camera
from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.inventory.models import Site
from astrocitizen.observatory import (
    CaptureObservation,
    ExecuteSession,
    prepare_wizard_session,
    reset_block_for_capture,
)
from astrocitizen.planning.models import Target
from astrocitizen.programs.models import Program
from astrocitizen.programs.seed import seed_program_templates
from astrocitizen.shared.ids import new_id
from astrocitizen.workspace.models import Workspace


def test_prepare_and_capture_n_frames(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "w.sqlite3")
    archive.migrate()
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    seed_program_templates(archive)
    site = archive.upsert_site(
        Site(
            id=new_id(),
            workspace_id=ws.id,
            name="Casa",
            latitude_deg=-29.0,
            longitude_deg=-51.0,
            is_default=True,
        )
    )
    prog = archive.upsert_program(
        Program(
            id=new_id(),
            workspace_id=ws.id,
            template_id="PO-A01",
            name="Vars",
            state="active",
        )
    )
    target = archive.upsert_target(
        Target(
            id=new_id(),
            workspace_id=ws.id,
            designation="StarA",
            ra_deg=100.0,
            dec_deg=-20.0,
        )
    )
    ctx = prepare_wizard_session(
        archive,
        workspace_id=ws.id,
        site_id=site.id,
        program_id=prog.id,
        target_id=target.id,
        night_date="2026-07-22",
    )
    assert ctx.session.state == "active"
    assert ctx.block.program_id == prog.id
    assert ctx.block.target_id == target.id

    # second prepare reuses session
    ctx2 = prepare_wizard_session(
        archive,
        workspace_id=ws.id,
        site_id=site.id,
        program_id=prog.id,
        target_id=target.id,
        night_date="2026-07-22",
    )
    assert ctx2.session.id == ctx.session.id
    assert ctx2.created_session is False

    store = LocalArtifactStore(tmp_path / "art")
    cam = create_camera("sim", width=16, height=16)
    capture = CaptureObservation(archive, cam, store)
    paths = []
    for _ in range(3):
        reset_block_for_capture(archive, ctx.block.id)
        obs = capture.execute(
            session_id=ctx.session.id,
            block_id=ctx.block.id,
            exptime_s=0.5,
        )
        assert obs.program_id == prog.id
        assert obs.target_id == target.id
        p = store.root / "raw" / "2026-07-22" / f"{obs.id}.fits"
        assert p.is_file()
        paths.append(p)
    assert len(paths) == 3

    ExecuteSession(archive).end(ctx.session.id)
    ended = archive.get_session(ctx.session.id)
    assert ended is not None and ended.state == "ended"
    archive.close()


def test_capture_with_direct_program_target(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "d.sqlite3")
    archive.migrate()
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    seed_program_templates(archive)
    site = archive.upsert_site(
        Site(
            id=new_id(),
            workspace_id=ws.id,
            name="S",
            latitude_deg=0.0,
            longitude_deg=0.0,
        )
    )
    prog = archive.upsert_program(
        Program(
            id=new_id(),
            workspace_id=ws.id,
            template_id="PO-A01",
            name="P",
            state="active",
        )
    )
    target = archive.upsert_target(
        Target(id=new_id(), workspace_id=ws.id, designation="T", ra_deg=10.0, dec_deg=5.0)
    )
    ctx = prepare_wizard_session(
        archive,
        workspace_id=ws.id,
        site_id=site.id,
        program_id=prog.id,
        target_id=target.id,
        night_date="2026-07-23",
    )
    store = LocalArtifactStore(tmp_path / "art")
    cam = create_camera("sim", width=8, height=8)
    obs = CaptureObservation(archive, cam, store).execute(
        session_id=ctx.session.id,
        program_id=prog.id,
        target_id=target.id,
        exptime_s=0.2,
    )
    assert obs.program_id == prog.id
    assert obs.target_id == target.id
    assert obs.headers_summary.get("OBJECT") == "T"
    archive.close()


def test_session_dashboard_builder() -> None:
    from astrocitizen.desktop.session_panel import build_session_dashboard

    assert callable(build_session_dashboard)
