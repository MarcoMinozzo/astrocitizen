"""Esqueletos PO-B01 / C01-C03 (AC-083/085/086)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from astropy.io import fits

from astrocitizen.adapters.fs import LocalArtifactStore
from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.analysis import BlinkDiff, ExtractSpectrum1D, MeasureAstrometry
from astrocitizen.contribution.bess import annotate_existing_fits
from astrocitizen.contribution.mpc import format_ades_psv
from astrocitizen.contribution.tns import format_tns_at_report
from astrocitizen.programs.workflows import P1_WORKFLOWS, workflow_for
from astrocitizen.shared.ids import new_id
from astrocitizen.workspace.models import Workspace


def _fits(path: Path, data: np.ndarray, **hdr) -> Path:
    hdu = fits.PrimaryHDU(data.astype(np.float32))
    for k, v in hdr.items():
        hdu.header[k] = v
    path.parent.mkdir(parents=True, exist_ok=True)
    hdu.writeto(path, overwrite=True)
    return path


def test_p1_workflows_b_c() -> None:
    for tid in ("PO-B01", "PO-C01", "PO-C02", "PO-C03"):
        wf = workflow_for(tid)
        assert wf is not None
        assert tid in P1_WORKFLOWS
    assert "extract_spectrum_1d" in workflow_for("PO-B01")["steps"]
    assert "export_mpc_ades" in workflow_for("PO-C01")["steps"]
    assert "blink_diff" in workflow_for("PO-C03")["steps"]
    assert workflow_for("PO-C02")["analysis"] == "astrometry"


def test_extract_spectrum_1d(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "s.sqlite3")
    archive.migrate()
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    store = LocalArtifactStore(tmp_path / "art")

    data = np.zeros((32, 100), dtype=np.float32)
    data[15:18, :] = 50.0
    data[15:18, 40:45] += 200.0
    path = _fits(
        tmp_path / "spec2d.fits",
        data,
        OBJECT="GAM CAS",
        **{"DATE-OBS": "2026-07-21T02:00:00Z"},
    )
    uri = store.put(path, key="raw/spec2d.fits")

    product = ExtractSpectrum1D(archive, store).execute(
        workspace_id=ws.id,
        fits_uri=uri,
        trace_y=16.0,
        half_width=2,
        wave0_nm=400.0,
        wave1_nm=700.0,
    )
    assert product.product_type == "spectrum_1d"
    assert product.summary["wave0_nm"] == 400.0
    points = archive.list_measurement_points(product.id)
    assert len(points) >= 2
    spec_path = store.resolve(product.parameters["spectrum_uri"])
    out = annotate_existing_fits(spec_path, tmp_path / "bess.fits", observer="MM")
    with fits.open(out) as hdul:
        assert hdul[0].header["OBSERVER"] == "MM"
    archive.close()


def test_measure_astrometry_tangent(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "a.sqlite3")
    archive.migrate()
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    store = LocalArtifactStore(tmp_path / "art")

    data = np.zeros((64, 64), dtype=np.float32)
    data[30:35, 40:45] = 2000.0
    path = _fits(
        tmp_path / "neo.fits",
        data,
        OBJECT="2026 XX",
        **{"DATE-OBS": "2026-07-21T03:00:00Z"},
    )
    uri = store.put(path, key="raw/neo.fits")

    product = MeasureAstrometry(archive, store).execute(
        workspace_id=ws.id,
        fits_uri=uri,
        x=42.0,
        y=32.0,
        ra0_deg=180.0,
        dec0_deg=10.0,
        scale_arcsec=1.0,
        designation="2026 XX",
        nonsidereal=True,
    )
    assert product.product_type == "astrometry"
    assert product.summary["ra_deg"] is not None
    assert product.parameters["nonsidereal"] is True
    psv = format_ades_psv(
        observatory_code="XXX",
        designation="2026 XX",
        observations=[
            {
                "epoch_utc": product.summary["epoch_utc"],
                "ra_deg": product.summary["ra_deg"],
                "dec_deg": product.summary["dec_deg"],
                "mag": product.summary.get("mag"),
                "band": "R",
            }
        ],
    )
    assert "2026 XX" in psv and "XXX" in psv
    archive.close()


def test_blink_diff_candidate(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "b.sqlite3")
    archive.migrate()
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    store = LocalArtifactStore(tmp_path / "art")

    ref = np.zeros((48, 48), dtype=np.float32)
    ref[20:24, 20:24] = 100.0
    new = ref.copy()
    new[10:14, 30:34] = 800.0
    ref_path = _fits(tmp_path / "ref.fits", ref, **{"DATE-OBS": "2026-07-20T01:00:00Z"})
    new_path = _fits(tmp_path / "new.fits", new, **{"DATE-OBS": "2026-07-21T01:00:00Z"})
    ref_uri = store.put(ref_path, key="raw/ref.fits")
    new_uri = store.put(new_path, key="raw/new.fits")

    product = BlinkDiff(archive, store).execute(
        workspace_id=ws.id,
        new_uri=new_uri,
        ref_uri=ref_uri,
        ra0_deg=50.0,
        dec0_deg=-20.0,
        scale_arcsec=1.5,
        internal_name="AT2026test",
    )
    assert product.product_type == "blink_candidate"
    assert product.summary["snr"] > 5
    assert product.summary["ra_deg"] is not None
    report = format_tns_at_report(
        ra_deg=float(product.summary["ra_deg"]),
        dec_deg=float(product.summary["dec_deg"]),
        groupid=0,
        reporter="AstroCitizen",
        discovery_mag=18.0,
        internal_name="AT2026test",
    )
    assert "AT2026test" in str(report)
    archive.close()
