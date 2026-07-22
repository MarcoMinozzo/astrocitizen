"""ENTRADA #7: echelle / speckle / polar entry channels."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from astropy.io import fits

from astrocitizen.adapters.fs import LocalArtifactStore
from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.observatory import (
    ImportEchelleOrders,
    ImportPolarimetrySet,
    ImportSpeckleCube,
)
from astrocitizen.observatory.specialties import estimate_stokes
from astrocitizen.shared.ids import new_id
from astrocitizen.workspace.models import Workspace


def _write_fits(path: Path, data: np.ndarray, **hdr: object) -> None:
    hdu = fits.PrimaryHDU(data)
    for k, v in hdr.items():
        hdu.header[k] = v
    hdu.writeto(path, overwrite=True)


def test_import_echelle_multi_ext(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "e.sqlite3")
    archive.migrate()
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    store = LocalArtifactStore(tmp_path / "art")
    path = tmp_path / "ech.fits"
    primary = fits.PrimaryHDU(np.arange(10, dtype=float))
    primary.header["OBJECT"] = "Vega"
    primary.header["ORDER"] = 1
    ext2 = fits.ImageHDU(np.arange(12, dtype=float) + 1)
    ext2.header["ORDER"] = 2
    fits.HDUList([primary, ext2]).writeto(path, overwrite=True)
    product = ImportEchelleOrders(archive, store).execute(
        workspace_id=ws.id, path=path
    )
    assert product.product_type == "echelle_orders"
    assert product.summary["n_orders"] == 2
    archive.close()


def test_import_speckle_cube(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "s.sqlite3")
    archive.migrate()
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    store = LocalArtifactStore(tmp_path / "art")
    cube = np.random.rand(8, 16, 16).astype(np.float32)
    path = tmp_path / "cube.fits"
    _write_fits(path, cube, OBJECT="WDS")
    product = ImportSpeckleCube(archive, store).execute(
        workspace_id=ws.id, path=path
    )
    assert product.product_type == "speckle_cube"
    assert product.summary["n_frames"] == 8
    assert product.summary["format"] == "fits_cube"
    archive.close()


def test_import_polar_with_csv(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "p.sqlite3")
    archive.migrate()
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    store = LocalArtifactStore(tmp_path / "art")
    folder = tmp_path / "pol"
    folder.mkdir()
    levels = {0: 100.0, 45: 110.0, 90: 80.0, 135: 90.0}
    rows = ["filename,angle_deg"]
    for ang, level in levels.items():
        name = f"p{ang}.fits"
        _write_fits(folder / name, np.full((8, 8), level, dtype=float))
        rows.append(f"{name},{ang}")
    csv_path = tmp_path / "angles.csv"
    csv_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    product = ImportPolarimetrySet(archive, store).execute(
        workspace_id=ws.id, path=folder, angles_csv=csv_path
    )
    assert product.product_type == "polarimetry_stokes"
    assert product.summary["n_frames"] == 4
    assert product.summary["complete_set"] is True
    assert product.summary["P"] is not None
    assert float(product.summary["P"]) > 0
    archive.close()


def test_estimate_stokes_incomplete() -> None:
    out = estimate_stokes(
        [
            {"angle_deg": 0, "mean_adu": 1.0},
            {"angle_deg": 90, "mean_adu": 0.5},
        ]
    )
    assert out["complete_set"] is False


def test_specialty_builder() -> None:
    from astrocitizen.desktop.specialty_panel import build_specialty_dashboard

    assert callable(build_specialty_dashboard)
