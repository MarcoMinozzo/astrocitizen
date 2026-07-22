"""Import FITS (IN-IMP)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from astropy.io import fits

from astrocitizen.adapters.fs import LocalArtifactStore
from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.desktop.import_panel import import_result_rows
from astrocitizen.inventory.models import Site
from astrocitizen.observatory import ImportFits
from astrocitizen.observatory.import_fits import discover_fits_paths
from astrocitizen.shared.errors import DomainError
from astrocitizen.shared.ids import new_id
from astrocitizen.workspace.models import Workspace


def _fits(path: Path, data: np.ndarray, **hdr) -> Path:
    hdu = fits.PrimaryHDU(data.astype(np.float32))
    for k, v in hdr.items():
        hdu.header[k] = v
    path.parent.mkdir(parents=True, exist_ok=True)
    hdu.writeto(path, overwrite=True)
    return path


def test_discover_fits_file_and_dir(tmp_path: Path) -> None:
    f1 = _fits(tmp_path / "a.fits", np.ones((8, 8)), OBJECT="A")
    _fits(tmp_path / "b.fit", np.ones((8, 8)), OBJECT="B")
    (tmp_path / "note.txt").write_text("x", encoding="utf-8")
    assert discover_fits_paths(f1) == [f1]
    found = discover_fits_paths(tmp_path)
    assert len(found) == 2
    with pytest.raises(DomainError):
        discover_fits_paths(tmp_path / "note.txt")


def test_import_fits_creates_observation(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "i.sqlite3")
    archive.migrate()
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    site = archive.upsert_site(
        Site(
            id=new_id(),
            workspace_id=ws.id,
            name="Lab",
            latitude_deg=-23.0,
            longitude_deg=-47.0,
            elevation_m=800.0,
            timezone="America/Sao_Paulo",
        )
    )
    store = LocalArtifactStore(tmp_path / "art")
    src = _fits(
        tmp_path / "star.fits",
        np.zeros((16, 16), dtype=np.float32),
        OBJECT="Vega",
        EXPTIME=5.0,
        **{"DATE-OBS": "2026-07-21T01:00:00"},
    )
    obs_list = ImportFits(archive, store).execute(
        workspace_id=ws.id,
        paths=[src],
        site_id=site.id,
        frame_type="light",
    )
    assert len(obs_list) == 1
    obs = obs_list[0]
    assert obs.state == "imported"
    assert obs.camera_backend == "import"
    assert obs.headers_summary.get("OBJECT") == "Vega"
    assert obs.headers_summary.get("IMAGETYP") == "LIGHT"
    rows = archive.list_observations(ws.id, include_simulated=True)
    assert any(str(r["id"]) == str(obs.id) for r in rows)
    uris = list((tmp_path / "art" / "imported").rglob("*.fits"))
    assert uris
    table = import_result_rows(obs_list)
    assert table[0][2] == "Vega"
    archive.close()
