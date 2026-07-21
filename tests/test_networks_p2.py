"""Testes BeSS / ExoClock / IOTA exporters."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import numpy as np
from astropy.io import fits

from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.contribution.bess import write_bess_fits
from astrocitizen.contribution.exoclock import ExportExoclock, format_exoclock_lc
from astrocitizen.contribution.iota import write_iota_pack
from astrocitizen.reduction.models import AnalysisProduct
from astrocitizen.shared.ids import new_id
from astrocitizen.workspace.models import Workspace


def test_bess_fits_keywords(tmp_path: Path) -> None:
    wave = np.linspace(400.0, 700.0, 301)
    flux = np.ones_like(wave)
    path = write_bess_fits(
        tmp_path / "be.fits",
        objname="gam Cas",
        observer="Test Obs",
        date_obs="2026-07-21T01:00:00",
        exptime_s=120.0,
        wavelength_nm=wave,
        flux=flux,
        site="NH",
        ra_deg=14.0,
        dec_deg=60.0,
    )
    with fits.open(path) as hdul:
        h = hdul[0].header
        assert h["OBJNAME"] == "gam Cas"
        assert h["OBSERVER"] == "Test Obs"
        assert h["BSS_SITE"] == "NH"
        assert h["CTYPE1"] == "WAVE"
        assert hdul[0].data.shape == (301,)


def test_exoclock_lc_format() -> None:
    text = format_exoclock_lc(
        target="WASP-12b",
        points=[
            {
                "t_utc": "2026-07-21T01:00:00Z",
                "y": 1.0,
                "y_err": 0.001,
                "meta": {"airmass": 1.2},
            }
        ],
    )
    assert "BJD_TDB" in text
    assert "WASP-12b" in text
    assert "exoclock.space" in text
    data_line = [ln for ln in text.splitlines() if not ln.startswith("#")][0]
    assert len(data_line.split()) == 4


def test_exoclock_from_product(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "t.sqlite3")
    archive.migrate()
    ws = archive.upsert_workspace(Workspace(id=uuid4(), name="w"))
    product = archive.save_analysis_product(
        AnalysisProduct(
            id=new_id(),
            workspace_id=ws.id,
            product_type="photometry",
            summary={"mag": 12.0},
        )
    )
    archive.save_measurement_points(
        product.id,
        [
            {
                "id": str(new_id()),
                "t_utc": "2026-07-21T02:00:00Z",
                "sequence_index": 0,
                "x": 0.0,
                "y": 0.98,
                "y_err": 0.002,
                "band": "R",
                "meta": {"airmass": 1.1},
            }
        ],
    )
    out = ExportExoclock(archive).execute(
        product_id=product.id,
        target="WASP-12b",
        out_path=tmp_path / "exo.txt",
    )
    assert out.is_file()
    assert "0.98" in out.read_text(encoding="utf-8")
    archive.close()


def test_iota_pack(tmp_path: Path) -> None:
    pack = write_iota_pack(
        tmp_path / "iota_evt",
        event_id="2026-07-21_123_Foo",
        star="TYC 123",
        asteroid="(123) Foo",
        observer="Tester",
        latitude_deg=-29.7,
        longitude_deg=-51.1,
        elevation_m=50.0,
        result="positive",
        d_time_utc="2026-07-21T03:00:00Z",
        r_time_utc="2026-07-21T03:00:12Z",
        lc_points=[{"t_utc": "2026-07-21T03:00:00Z", "y": 100, "y_err": 1}],
    )
    assert (pack / "meta.json").is_file()
    assert (pack / "lc.csv").is_file()
    assert list(pack.glob("IOTA-ES_report_*.txt"))
