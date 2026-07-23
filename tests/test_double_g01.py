"""PO-G01 Duplas: LogDoubleMeasure (AC-152)."""

from __future__ import annotations

from pathlib import Path

from astrocitizen.adapters.fs import LocalArtifactStore
from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.inventory.models import Site
from astrocitizen.observatory import LogDoubleMeasure
from astrocitizen.programs.workflows import workflow_for
from astrocitizen.shared.errors import DomainError
from astrocitizen.shared.ids import new_id
from astrocitizen.workspace.models import Workspace


def test_log_double_measure(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "d.sqlite3")
    archive.migrate()
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    site = archive.upsert_site(
        Site(
            id=new_id(),
            workspace_id=ws.id,
            name="Casa",
            latitude_deg=-29.0,
            longitude_deg=-51.0,
        )
    )
    store = LocalArtifactStore(tmp_path / "art")
    product = LogDoubleMeasure(archive, store).execute(
        workspace_id=ws.id,
        object_name="WDS 04184+2135",
        pa_deg=127.3,
        sep_arcsec=2.45,
        epoch_utc="2026-07-23T02:15:00Z",
        method="micrometer",
        mag_primary=2.0,
        mag_secondary=2.9,
        site_id=site.id,
        notes="good night",
    )
    assert product.product_type == "double_measure"
    assert product.summary["pa_deg"] == 127.3
    assert product.summary["sep_arcsec"] == 2.45
    assert product.parameters["channel"] == "IN-LOG"
    pts = archive.list_measurement_points(product.id)
    assert len(pts) == 1
    assert pts[0]["x"] == 127.3
    assert pts[0]["y"] == 2.45
    archive.close()


def test_log_double_with_image(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "i.sqlite3")
    archive.migrate()
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    store = LocalArtifactStore(tmp_path / "art")
    img = tmp_path / "pair.fits"
    img.write_bytes(b"SIMPLE  =                    T / mock\nEND")
    product = LogDoubleMeasure(archive, store).execute(
        workspace_id=ws.id,
        object_name="Castor",
        pa_deg=10.0,
        sep_arcsec=5.5,
        method="imaging_manual",
        image_path=img,
    )
    assert product.parameters["channel"] == "IN-IMP"
    assert product.parameters["image_uri"]
    assert product.summary["has_image"] is True
    archive.close()


def test_log_double_validation(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "v.sqlite3")
    archive.migrate()
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    store = LocalArtifactStore(tmp_path / "art")
    try:
        LogDoubleMeasure(archive, store).execute(
            workspace_id=ws.id,
            object_name="X",
            pa_deg=400.0,
            sep_arcsec=1.0,
        )
        raise AssertionError("expected DomainError")
    except DomainError:
        pass
    try:
        LogDoubleMeasure(archive, store).execute(
            workspace_id=ws.id,
            object_name="X",
            pa_deg=10.0,
            sep_arcsec=0.0,
        )
        raise AssertionError("expected DomainError")
    except DomainError:
        pass
    archive.close()


def test_workflow_g01() -> None:
    wf = workflow_for("PO-G01")
    assert wf is not None
    assert "log_double_measure" in wf["steps"]
    assert wf["export"] == "double_measure"


def test_observe_builder() -> None:
    from astrocitizen.desktop.observe_panel import build_observe_dashboard

    assert callable(build_observe_dashboard)
