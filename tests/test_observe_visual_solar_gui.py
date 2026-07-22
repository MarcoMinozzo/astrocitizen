"""Observar: visual_log + workflow PO-F03 + painel builder."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from astropy.io import fits

from astrocitizen.adapters.fs import LocalArtifactStore
from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.analysis import CountSunspots
from astrocitizen.inventory.models import Site
from astrocitizen.observatory import LogVisualObservation
from astrocitizen.programs.workflows import workflow_for
from astrocitizen.shared.errors import DomainError
from astrocitizen.shared.ids import new_id
from astrocitizen.workspace.models import Workspace


def test_workflow_f03() -> None:
    wf = workflow_for("PO-F03")
    assert wf is not None
    assert "log_visual" in wf["steps"]


def test_log_visual_product(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "v.sqlite3")
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
    product = LogVisualObservation(archive).execute(
        workspace_id=ws.id,
        object_name="M42",
        description="Nebulosa visivel a olho nu com binoculos.",
        conditions="ceu limpo",
        site_id=site.id,
        observer="Tester",
        magnitude=4.0,
    )
    assert product.product_type == "visual_log"
    assert product.summary["object"] == "M42"
    assert product.parameters["observation_id"]
    try:
        LogVisualObservation(archive).execute(
            workspace_id=ws.id, object_name="", description="x"
        )
        raise AssertionError("expected DomainError")
    except DomainError:
        pass
    archive.close()


def test_solar_gui_path_via_count(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "s.sqlite3")
    archive.migrate()
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    store = LocalArtifactStore(tmp_path / "art")
    # tiny synthetic disk
    y, x = np.ogrid[-16:16, -16:16]
    disk = (x * x + y * y) <= 12 * 12
    data = np.ones((32, 32), dtype=np.float32) * 100
    data[disk] = 200
    data[14:18, 14:18] = 40  # dark spot
    fits_path = tmp_path / "sun.fits"
    fits.PrimaryHDU(data).writeto(fits_path, overwrite=True)
    uri = store.put(fits_path, key="solar/sun.fits")
    product = CountSunspots(archive, store).execute(
        workspace_id=ws.id,
        fits_uri=uri,
        filter_confirmed=True,
        no_unfiltered_eyepiece=True,
        daytime_acknowledged=True,
    )
    assert product.product_type == "solar_sunspots"
    assert product.summary.get("safety_ok") is True
    archive.close()


def test_observe_builder() -> None:
    from astrocitizen.desktop.observe_panel import build_observe_dashboard

    assert callable(build_observe_dashboard)
