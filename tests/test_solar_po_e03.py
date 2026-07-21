"""Esqueleto PO-E03 Sol / manchas (AC-088)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from astropy.io import fits

from astrocitizen.adapters.fs import LocalArtifactStore
from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.analysis.solar import (
    CountSunspots,
    detect_sunspots,
    validate_solar_safety,
    wolf_number,
)
from astrocitizen.contribution.solar import ExportSolarReport, format_solar_report
from astrocitizen.programs.workflows import workflow_for
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


def test_po_e03_workflow() -> None:
    wf = workflow_for("PO-E03")
    assert wf is not None
    assert "safety_checklist" in wf["steps"]
    assert "count_sunspots" in wf["steps"]
    assert wf["analysis"] == "solar"


def test_safety_requires_flags() -> None:
    with pytest.raises(DomainError):
        validate_solar_safety(
            filter_confirmed=False,
            no_unfiltered_eyepiece=True,
            daytime_acknowledged=True,
        )
    ok = validate_solar_safety(
        filter_confirmed=True,
        no_unfiltered_eyepiece=True,
        daytime_acknowledged=True,
        filter_name="Baader continuum",
    )
    assert ok["filter_confirmed"] is True


def test_wolf_and_detect() -> None:
    assert wolf_number(groups=2, spots=5, k=1.0) == 25.0
    data = np.full((64, 64), 1000.0, dtype=np.float32)
    # two dark spots on bright disk
    data[20:24, 20:24] = 400.0
    data[40:45, 40:45] = 350.0
    det = detect_sunspots(data, spot_frac=0.6, min_pixels=4)
    assert det["spots"] >= 2
    assert det["disk_pixels"] > 100


def test_count_sunspots_and_export(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "s.sqlite3")
    archive.migrate()
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    store = LocalArtifactStore(tmp_path / "art")

    data = np.full((48, 48), 800.0, dtype=np.float32)
    data[10:14, 10:14] = 200.0
    data[30:35, 30:35] = 180.0
    path = _fits(
        tmp_path / "sun.fits",
        data,
        OBJECT="SUN",
        **{"DATE-OBS": "2026-07-21T15:00:00Z"},
    )
    uri = store.put(path, key="raw/sun.fits")

    product = CountSunspots(archive, store).execute(
        workspace_id=ws.id,
        fits_uri=uri,
        filter_confirmed=True,
        no_unfiltered_eyepiece=True,
        daytime_acknowledged=True,
        filter_name="white-light",
        observer="MM",
        spots=3,
        groups=2,
        k=1.0,
    )
    assert product.product_type == "solar_sunspots"
    assert product.summary["wolf_r"] == 23.0
    assert product.summary["safety_ok"] is True

    out = ExportSolarReport(archive).execute(
        product_id=product.id,
        out_path=tmp_path / "solar.txt",
        site="Gramadao",
    )
    text = out.read_text(encoding="utf-8")
    assert "#TYPE=ASTROCITIZEN_SOLAR" in text
    assert "2 3 23.00" in text
    assert "SAFETY=" in text

    fmt = format_solar_report(
        observer="X",
        epoch_utc="2026-07-21T15:00:00Z",
        groups=1,
        spots=1,
        wolf_r=11.0,
    )
    assert "1 1 11.00" in fmt
    archive.close()
