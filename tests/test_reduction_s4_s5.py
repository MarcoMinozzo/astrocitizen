"""Testes S4/S5 - calibracao, fotometria, AAVSO, workflows."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from astropy.io import fits

from astrocitizen.adapters.fs import LocalArtifactStore
from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.adapters.sqlite.schema import SCHEMA_VERSION
from astrocitizen.analysis import AperturePhotometry
from astrocitizen.contribution.aavso import ExportAavso, format_aavso_extended
from astrocitizen.programs.workflows import P1_WORKFLOWS, workflow_for
from astrocitizen.reduction import ApplyCalibration, BuildMaster, fits_stats
from astrocitizen.shared.ids import new_id
from astrocitizen.workspace.models import Workspace


def _fits(path: Path, data: np.ndarray, **hdr) -> Path:
    hdu = fits.PrimaryHDU(data.astype(np.float32))
    for k, v in hdr.items():
        hdu.header[k] = v
    path.parent.mkdir(parents=True, exist_ok=True)
    hdu.writeto(path, overwrite=True)
    return path


def test_schema_v4(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "r.sqlite3")
    assert archive.migrate() == SCHEMA_VERSION == 4
    archive.close()


def test_build_master_and_calibrate(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "r.sqlite3")
    archive.migrate()
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    store = LocalArtifactStore(tmp_path / "art")

    bias_paths = []
    for i in range(3):
        bias_paths.append(
            _fits(tmp_path / f"bias{i}.fits", np.full((32, 32), 100.0 + i * 0.1))
        )
    master = BuildMaster(archive, store).execute(
        workspace_id=ws.id, kind="bias", fits_paths=bias_paths
    )
    assert master.version_num == 1
    assert master.kind == "bias"

    light = _fits(tmp_path / "light.fits", np.full((32, 32), 500.0), OBJECT="STAR")
    light_uri = store.put(light, key="raw/light.fits")
    product = ApplyCalibration(archive, store).execute(
        workspace_id=ws.id,
        light_uri=light_uri,
        bias_master_id=master.id,
    )
    assert product.product_type == "calibrated_frame"
    assert product.summary["mean"] < 500
    uri = product.parameters["uri"]
    st = fits_stats(store.resolve(uri))
    assert st["shape"] == [32, 32]
    archive.close()


def test_photometry_and_aavso(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "r.sqlite3")
    archive.migrate()
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    store = LocalArtifactStore(tmp_path / "art")

    data = np.zeros((64, 64), dtype=np.float32)
    data[30:35, 40:45] = 1000.0
    data[10:13, 10:13] = 800.0
    path = _fits(
        tmp_path / "star.fits",
        data,
        OBJECT="VAR",
        **{"DATE-OBS": "2026-07-15T01:00:00Z"},
    )
    uri = store.put(path, key="reduced/star.fits")

    product = AperturePhotometry(archive, store).execute(
        workspace_id=ws.id,
        fits_uri=uri,
        x=42.0,
        y=32.0,
        band="V",
        comp_xy=(11.0, 11.0),
    )
    assert product.product_type == "light_curve"
    assert product.summary.get("flux", 0) > 0
    points = archive.list_measurement_points(product.id)
    assert len(points) == 1

    out = ExportAavso(archive).execute(
        product_id=product.id,
        star_name="TEST VAR",
        observer_code="XYZ",
        out_path=tmp_path / "out.txt",
    )
    text = out.read_text(encoding="utf-8")
    assert "#TYPE=EXTENDED" in text
    assert "XYZ" in text
    archive.close()


def test_aavso_format_helper() -> None:
    text = format_aavso_extended(
        star_name="SS CYG",
        observer_code="ABC",
        points=[{"t_utc": "2026-01-01T00:00:00Z", "y": 12.3, "y_err": 0.01, "band": "V"}],
    )
    assert "SS CYG" in text and "12.3000" in text


def test_p1_workflows() -> None:
    assert workflow_for("PO-A01") is not None
    assert "export_aavso" in workflow_for("PO-A01")["steps"]
    assert "PO-J01" in P1_WORKFLOWS
    assert "PO-J03" in P1_WORKFLOWS
    assert "PO-J05" in P1_WORKFLOWS
