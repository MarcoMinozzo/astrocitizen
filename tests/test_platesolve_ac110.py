"""Plate-solve / WCS (AC-110)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from astropy.io import fits

from astrocitizen.adapters.fs import LocalArtifactStore
from astrocitizen.adapters.platesolve import (
    SyntheticPlateSolver,
    create_plate_solver,
)
from astrocitizen.adapters.platesolve.wcs_io import build_tan_wcs, write_fits_with_wcs
from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.analysis import MeasureAstrometry, PlateSolve
from astrocitizen.analysis.astrometry import pixel_to_radec_wcs
from astrocitizen.programs.workflows import workflow_for
from astrocitizen.shared.ids import new_id
from astrocitizen.workspace.models import Workspace


def _fits(path: Path, data: np.ndarray, **hdr) -> Path:
    hdu = fits.PrimaryHDU(data.astype(np.float32))
    for k, v in hdr.items():
        hdu.header[k] = v
    path.parent.mkdir(parents=True, exist_ok=True)
    hdu.writeto(path, overwrite=True)
    return path


def test_workflow_includes_plate_solve() -> None:
    assert "plate_solve" in workflow_for("PO-C01")["steps"]
    assert "plate_solve" in workflow_for("PO-C02")["steps"]


def test_synthetic_solver_writes_wcs(tmp_path: Path) -> None:
    data = np.zeros((40, 40), dtype=np.float32)
    data[18:22, 18:22] = 500.0
    src = _fits(tmp_path / "raw.fits", data, OBJECT="TEST")
    solver = SyntheticPlateSolver(default_scale_arcsec=1.5)
    result = solver.solve(
        src,
        out_dir=tmp_path / "out",
        ra_hint_deg=123.4,
        dec_hint_deg=-5.6,
    )
    assert result.backend == "synthetic"
    assert result.wcs_fits_path is not None
    assert result.wcs_fits_path.is_file()
    with fits.open(result.wcs_fits_path) as hdul:
        assert "CTYPE1" in hdul[0].header
        sky = pixel_to_radec_wcs(hdul[0].header, 19.5, 19.5)
    assert sky is not None
    assert abs(sky[0] - 123.4) < 0.05
    assert abs(sky[1] - (-5.6)) < 0.05


def test_plate_solve_use_case_and_measure(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "p.sqlite3")
    archive.migrate()
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    store = LocalArtifactStore(tmp_path / "art")

    data = np.zeros((64, 64), dtype=np.float32)
    data[30:35, 40:45] = 2000.0
    path = _fits(
        tmp_path / "neo.fits",
        data,
        OBJECT="2026 YY",
        **{"DATE-OBS": "2026-07-21T04:00:00Z"},
    )
    uri = store.put(path, key="raw/neo.fits")

    product, result = PlateSolve(archive, store, SyntheticPlateSolver()).execute(
        workspace_id=ws.id,
        fits_uri=uri,
        ra_hint_deg=180.0,
        dec_hint_deg=10.0,
        scale_low_arcsec=1.0,
        scale_high_arcsec=1.0,
    )
    assert product.product_type == "wcs_solution"
    assert result.backend == "synthetic"
    wcs_uri = product.parameters["wcs_uri"]

    measured = MeasureAstrometry(archive, store).execute(
        workspace_id=ws.id,
        fits_uri=wcs_uri,
        x=42.0,
        y=32.0,
        designation="2026 YY",
    )
    assert measured.product_type == "astrometry"
    assert measured.parameters["method"] == "wcs"
    assert abs(float(measured.summary["ra_deg"]) - 180.0) < 1.0
    archive.close()


def test_create_plate_solver_factory() -> None:
    syn = create_plate_solver("synthetic")
    assert isinstance(syn, SyntheticPlateSolver)
    auto = create_plate_solver("auto")
    assert auto is not None


def test_build_tan_wcs_roundtrip(tmp_path: Path) -> None:
    data = np.ones((20, 20), dtype=np.float32)
    src = _fits(tmp_path / "a.fits", data)
    wcs = build_tan_wcs(
        ra_deg=10.0,
        dec_deg=20.0,
        scale_arcsec=2.0,
        crpix1=10.5,
        crpix2=10.5,
    )
    dest = write_fits_with_wcs(src, tmp_path / "b.fits", wcs)
    with fits.open(dest) as hdul:
        assert hdul[0].header["CTYPE1"].startswith("RA")
