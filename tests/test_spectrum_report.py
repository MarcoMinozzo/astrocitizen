"""Interpretacao espectral (spectrum_report)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from astropy.io import fits

from astrocitizen.adapters.fs import LocalArtifactStore
from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.analysis.spectrum_report import (
    InterpretSpectrum,
    classify_hint,
    detect_line_features,
    format_spectrum_report,
    load_spectrum_arrays,
)
from astrocitizen.programs.workflows import workflow_for
from astrocitizen.shared.ids import new_id
from astrocitizen.workspace.models import Workspace


def _spec_fits(path: Path, *, date: str, scale: float = 1.0) -> Path:
    # Angstrom grid 4000-8000
    wave = np.linspace(4000.0, 8000.0, 2001)
    # blue-heavy continuum
    flux = scale * (2.5 - (wave - 4000.0) / 4000.0)
    # H-alpha emission
    flux += 1.5 * np.exp(-0.5 * ((wave - 6563.0) / 8.0) ** 2)
    # H-beta emission
    flux += 0.6 * np.exp(-0.5 * ((wave - 4861.0) / 8.0) ** 2)
    # telluric O2 absorption
    flux -= 0.8 * np.exp(-0.5 * ((wave - 7605.0) / 6.0) ** 2)
    hdu = fits.PrimaryHDU(flux.astype(np.float32))
    hdu.header["CRVAL1"] = float(wave[0])
    hdu.header["CDELT1"] = float(wave[1] - wave[0])
    hdu.header["CRPIX1"] = 1.0
    hdu.header["CTYPE1"] = "WAVE"
    hdu.header["CUNIT1"] = "Angstrom"
    hdu.header["OBJECT"] = "SN2026sqf"
    hdu.header["DATE-OBS"] = date
    hdu.header["INSTRUME"] = "TinyStarEx"
    path.parent.mkdir(parents=True, exist_ok=True)
    hdu.writeto(path, overwrite=True)
    return path


def test_workflow_b03_has_interpret() -> None:
    wf = workflow_for("PO-B03")
    assert wf is not None
    assert "interpret_spectrum" in wf["steps"]
    assert "interpret_spectrum" in workflow_for("PO-B01")["steps"]


def test_detect_balmer_and_telluric(tmp_path: Path) -> None:
    path = _spec_fits(tmp_path / "sn.fits", date="2026-07-17T20:00:00")
    wave, flux, meta = load_spectrum_arrays(path)
    assert meta["object"] == "SN2026sqf"
    feats = detect_line_features(wave, flux, half_width_A=50.0, snr_min=2.5)
    names = {f["name"] for f in feats}
    assert "H-alpha" in names
    assert "H-beta" in names
    hint = classify_hint(feats)
    assert "H-rich" in hint["label"] or "Balmer" in str(hint["notes"])
    text = format_spectrum_report(
        meta=meta,
        features=feats,
        hint=hint,
        continuum={"blue_med": 1.0, "red_med": 1.0, "blue_red_ratio": 1.2},
    )
    assert "H-alpha" in text
    assert "TELLURIC" in text.upper() or "O2" in text or "telluric" in text.lower()


def test_interpret_spectrum_product(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "r.sqlite3")
    archive.migrate()
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    store = LocalArtifactStore(tmp_path / "art")
    p1 = _spec_fits(tmp_path / "e1.fits", date="2026-07-17T20:00:00", scale=1.0)
    p2 = _spec_fits(tmp_path / "e2.fits", date="2026-07-20T20:00:00", scale=0.7)
    uri1 = store.put(p1, key="spec/e1.fits")
    # second epoch as extra via product would need spectrum_1d; use two calls:
    # primary + put second and create fake product with spectrum_uri
    from astrocitizen.reduction.models import AnalysisProduct

    prod2 = archive.save_analysis_product(
        AnalysisProduct(
            id=new_id(),
            workspace_id=ws.id,
            product_type="spectrum_1d",
            version_num=1,
            parameters={"spectrum_uri": store.put(p2, key="spec/e2.fits")},
            summary={},
            state="ready",
        )
    )
    report = InterpretSpectrum(archive, store).execute(
        workspace_id=ws.id,
        fits_uri=uri1,
        extra_product_ids=[prod2.id],
    )
    assert report.product_type == "spectrum_report"
    assert report.summary.get("n_epochs") == 2
    assert report.summary.get("top_line") is not None
    path = Path(report.parameters["report_path"])
    assert path.is_file()
    body = path.read_text(encoding="utf-8")
    assert "ASTROCITIZEN_SPECTRUM_REPORT" in body
    assert "EPOCHS" in body
    archive.close()
