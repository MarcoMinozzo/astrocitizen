"""Radio AC-161: espectro / scan / lab notes (PO-I02..I04)."""

from __future__ import annotations

from pathlib import Path

from astrocitizen.adapters.fs import LocalArtifactStore
from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.inventory.models import Site
from astrocitizen.observatory import ImportRadioScan, ImportRadioSpectrum, ImportRadioTimeseries
from astrocitizen.observatory.radio import parse_radio_scan_csv, parse_radio_spectrum_csv
from astrocitizen.programs.workflows import workflow_for
from astrocitizen.shared.ids import new_id
from astrocitizen.workspace.models import Workspace


def _ws(tmp_path: Path):
    archive = SqliteArchive(tmp_path / "r.sqlite3")
    archive.migrate()
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    site = archive.upsert_site(
        Site(
            id=new_id(),
            workspace_id=ws.id,
            name="SDR",
            latitude_deg=-29.0,
            longitude_deg=-51.0,
        )
    )
    store = LocalArtifactStore(tmp_path / "art")
    return archive, ws, site, store


def test_parse_spectrum_csv(tmp_path: Path) -> None:
    p = tmp_path / "hi.csv"
    p.write_text(
        "freq_mhz,power\n"
        "1420.0,-40.0\n"
        "1420.2,-35.5\n"
        "1420.4,-38.0\n",
        encoding="utf-8",
    )
    pts = parse_radio_spectrum_csv(p)
    assert len(pts) == 3
    assert pts[0]["x"] == 1420.0
    assert pts[1]["meta"]["freq_mhz"] == 1420.2


def test_import_spectrum(tmp_path: Path) -> None:
    archive, ws, site, store = _ws(tmp_path)
    csv_path = tmp_path / "spec.csv"
    csv_path.write_text(
        "frequency,intensity\n"
        "1419.5,1.0\n"
        "1420.0,2.0\n"
        "1420.5,1.5\n",
        encoding="utf-8",
    )
    product = ImportRadioSpectrum(archive, store).execute(
        workspace_id=ws.id,
        path=csv_path,
        site_id=site.id,
        frequency_mhz=1420.4,
        lab_notes="RTL-SDR + LNA",
    )
    assert product.product_type == "radio_spectrum"
    assert product.summary["n_points"] == 3
    assert product.summary["freq0_mhz"] == 1419.5
    assert product.parameters["lab_notes"] == "RTL-SDR + LNA"
    pts = archive.list_measurement_points(product.id)
    assert pts[0]["x"] == 1419.5
    archive.close()


def test_parse_and_import_scan(tmp_path: Path) -> None:
    archive, ws, site, store = _ws(tmp_path)
    csv_path = tmp_path / "drift.csv"
    csv_path.write_text(
        "t_utc,power,az_deg,el_deg\n"
        "2026-07-23T10:00:00Z,-50,180,45\n"
        "2026-07-23T10:00:01Z,-48,181,45\n"
        "2026-07-23T10:00:02Z,-47,182,45\n",
        encoding="utf-8",
    )
    pts = parse_radio_scan_csv(csv_path)
    assert pts[1]["meta"]["az_deg"] == 181.0
    product = ImportRadioScan(archive, store).execute(
        workspace_id=ws.id,
        path=csv_path,
        site_id=site.id,
        frequency_mhz=1420.0,
    )
    assert product.product_type == "radio_scan"
    assert product.summary["n_with_pointing"] == 3
    archive.close()


def test_series_lab_notes(tmp_path: Path) -> None:
    archive, ws, site, store = _ws(tmp_path)
    csv_path = tmp_path / "vhf.csv"
    csv_path.write_text(
        "t_utc,power\n"
        "2026-07-23T12:00:00Z,1\n"
        "2026-07-23T12:00:01Z,2\n",
        encoding="utf-8",
    )
    product = ImportRadioTimeseries(archive, store).execute(
        workspace_id=ws.id,
        path=csv_path,
        site_id=site.id,
        lab_notes="Yagi 2m",
    )
    assert product.product_type == "radio_timeseries"
    assert product.parameters["lab_notes"] == "Yagi 2m"
    archive.close()


def test_workflows_i02_i04() -> None:
    for tid in ("PO-I02", "PO-I03", "PO-I04"):
        wf = workflow_for(tid)
        assert wf is not None
        assert wf["analysis"] == "radio"


def test_radio_builder() -> None:
    from astrocitizen.desktop.radio_panel import build_radio_dashboard

    assert callable(build_radio_dashboard)
