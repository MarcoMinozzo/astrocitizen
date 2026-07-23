"""AC-100: extracao espectro 1D (auto-trace + sky)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from astropy.io import fits

from astrocitizen.adapters.fs import LocalArtifactStore
from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.analysis.spectroscopy import (
    ExtractSpectrum1D,
    estimate_extraction_snr,
    extract_trace,
    find_trace_peak,
    spatial_profile,
)
from astrocitizen.shared.ids import new_id
from astrocitizen.workspace.models import Workspace


def _fits2d(path: Path, data: np.ndarray, **hdr: object) -> Path:
    hdu = fits.PrimaryHDU(data.astype(np.float32))
    for k, v in hdr.items():
        hdu.header[k] = v
    path.parent.mkdir(parents=True, exist_ok=True)
    hdu.writeto(path, overwrite=True)
    return path


def test_find_trace_peak_near_bright_row() -> None:
    data = np.zeros((40, 80), dtype=float)
    data[22:25, :] = 10.0
    data[23, :] = 30.0
    peak = find_trace_peak(data, axis="x")
    assert 22.0 <= peak <= 25.0


def test_extract_with_sky_removes_bias() -> None:
    data = np.zeros((50, 100), dtype=float)
    data[:, :] = 5.0  # sky
    data[20:23, :] = 25.0  # object = sky + 20
    data[20:23, 40:50] = 125.0  # emission bump
    flux_raw, _ = extract_trace(
        data, trace_y=21.0, half_width=1, subtract_sky=False
    )
    flux_sky, meta = extract_trace(
        data,
        trace_y=21.0,
        half_width=1,
        subtract_sky=True,
        sky_offset=8,
        sky_half_width=2,
    )
    assert meta["subtract_sky"] is True
    assert float(np.median(flux_sky[:30])) == pytest.approx(60.0, abs=5.0)
    assert float(np.median(flux_raw[:30])) > float(np.median(flux_sky[:30]))


def test_snr_est_positive_on_line() -> None:
    flux = np.ones(100) * 10.0
    flux[40:45] = 80.0
    snr = estimate_extraction_snr(flux)
    assert snr is not None and snr > 5


def test_extract_spectrum_auto_trace_product(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "ac100.sqlite3")
    archive.migrate()
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    store = LocalArtifactStore(tmp_path / "art")

    data = np.zeros((48, 120), dtype=np.float32)
    data[30:33, :] = 40.0
    data[30:33, 55:60] += 300.0
    path = _fits2d(
        tmp_path / "s2d.fits",
        data,
        OBJECT="GAM CAS",
        **{"DATE-OBS": "2026-07-23T01:00:00Z"},
    )
    uri = store.put(path, key="raw/s2d.fits")
    product = ExtractSpectrum1D(archive, store).execute(
        workspace_id=ws.id,
        fits_uri=uri,
        auto_trace=True,
        half_width=2,
        subtract_sky=True,
        wave0_nm=400.0,
        wave1_nm=700.0,
    )
    assert product.product_type == "spectrum_1d"
    assert product.parameters["method"] == "slit_sum_v1"
    assert product.summary["auto_trace"] is True
    assert 29.0 <= float(product.summary["trace_y"]) <= 33.0
    assert product.summary.get("snr_est") is not None
    assert product.parameters["wavelength_calibrated"] is True
    with fits.open(store.resolve(product.parameters["spectrum_uri"])) as hdul:
        assert hdul[0].header["ACMETHOD"] == "slit_sum_v1"
        assert hdul[0].header["SKYSUB"] is True
    archive.close()


def test_spatial_profile_length() -> None:
    data = np.ones((10, 20))
    assert len(spatial_profile(data, axis="x")) == 10
    assert len(spatial_profile(data, axis="y")) == 20
