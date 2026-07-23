"""AC-101: calibracao de comprimento de onda."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from astropy.io import fits

from astrocitizen.adapters.fs import LocalArtifactStore
from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.analysis.spectrum_report import load_spectrum_arrays
from astrocitizen.analysis.wavelength_calib import (
    CalibrateWavelength,
    detect_emission_peaks,
    fit_wavelength_poly,
    match_peaks_to_catalog,
    parse_wave_pairs,
    write_calibrated_spectrum,
)
from astrocitizen.shared.ids import new_id
from astrocitizen.workspace.models import Workspace


def test_parse_and_fit_quadratic() -> None:
    pairs = parse_wave_pairs("0:400,50:450.5,100:502")
    sol = fit_wavelength_poly(
        [p for p, _ in pairs],
        [w for _, w in pairs],
        degree=2,
    )
    assert sol.degree == 2
    assert sol.rms_nm < 0.05
    assert abs(float(sol.wave_at(0)) - 400.0) < 0.1
    assert abs(float(sol.wave_at(100)) - 502.0) < 0.1


def test_lamp_peak_match_and_calibrate_product(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "w.sqlite3")
    archive.migrate()
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    store = LocalArtifactStore(tmp_path / "art")

    n = 200
    # science continuum
    sci = np.ones(n, dtype=np.float32) * 20.0
    sci[80:85] = 100.0
    # lamp with neon-like peaks at known pix mapped by quadratic-ish linear
    # wave = 580 + pix * 0.6  → pix for 585.249 ≈ 8.75, 609.616 ≈ 49.36, ...
    lamp = np.ones(n, dtype=np.float32) * 5.0
    true_lines = [585.249, 609.616, 640.225, 671.704]
    for w in true_lines:
        pix = int(round((w - 580.0) / 0.6))
        if 2 <= pix < n - 2:
            lamp[pix - 1 : pix + 2] = 200.0
            lamp[pix] = 400.0

    sci_path = tmp_path / "sci.fits"
    lamp_path = tmp_path / "lamp.fits"
    fits.PrimaryHDU(sci).writeto(sci_path, overwrite=True)
    fits.PrimaryHDU(lamp).writeto(lamp_path, overwrite=True)
    sci_uri = store.put(sci_path, key="raw/sci.fits")
    lamp_uri = store.put(lamp_path, key="raw/lamp.fits")

    peaks = detect_emission_peaks(lamp)
    assert len(peaks) >= 3
    pairs = match_peaks_to_catalog(
        peaks,
        true_lines,
        wave0_nm=580.0,
        wave1_nm=580.0 + 0.6 * (n - 1),
        n_pix=n,
        max_residual_nm=3.0,
    )
    assert len(pairs) >= 3

    product = CalibrateWavelength(archive, store).execute(
        workspace_id=ws.id,
        fits_uri=sci_uri,
        lamp_uri=lamp_uri,
        catalog="neon",
        wave0_nm=580.0,
        wave1_nm=580.0 + 0.6 * (n - 1),
        degree=1,
    )
    assert product.parameters["wavelength_calibrated"] is True
    assert product.summary["n_anchors"] >= 2
    assert product.summary["rms_nm"] < 1.5

    out = store.resolve(product.parameters["spectrum_uri"])
    with fits.open(out) as hdul:
        assert hdul[0].header.get("AC_WDEG") == 1
    wave_A, flux, _ = load_spectrum_arrays(out)
    assert len(wave_A) == n
    # H-alpha region ~656 nm → ~6560 A should be in range
    assert wave_A[0] < 6560 < wave_A[-1]
    archive.close()


def test_write_and_reload_poly_headers(tmp_path: Path) -> None:
    sol = fit_wavelength_poly([0, 50, 100], [400.0, 450.0, 501.0], degree=2)
    flux = np.linspace(1, 2, 101).astype(np.float32)
    out = tmp_path / "cal.fits"
    write_calibrated_spectrum(flux, sol, out, meta_header={"OBJECT": "TEST"})
    wave_A, data, meta = load_spectrum_arrays(out)
    assert abs(meta["wave0_A"] / 10.0 - 400.0) < 0.5
    assert abs(float(data[0]) - 1.0) < 1e-5
    assert abs(wave_A[0] / 10.0 - float(sol.wave_at(0))) < 0.2
