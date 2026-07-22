"""Radio IN-RAD / PO-I01 (ENTRADA #6)."""

from __future__ import annotations

from pathlib import Path

from astrocitizen.adapters.fs import LocalArtifactStore
from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.inventory.models import Site
from astrocitizen.observatory import ImportRadioTimeseries
from astrocitizen.observatory.radio import parse_radio_power_csv
from astrocitizen.shared.errors import DomainError
from astrocitizen.shared.ids import new_id
from astrocitizen.workspace.models import Workspace


def test_parse_radio_csv(tmp_path: Path) -> None:
    p = tmp_path / "r.csv"
    p.write_text(
        "t_utc,power,power_err\n"
        "2026-07-22T12:00:00Z,-50.1,0.2\n"
        "2026-07-22T12:00:01Z,-49.8,0.2\n"
        "2026-07-22T12:00:02Z,-48.0,0.3\n",
        encoding="utf-8",
    )
    pts = parse_radio_power_csv(p)
    assert len(pts) == 3
    assert pts[0]["band"] == "radio"


def test_import_radio_csv(tmp_path: Path) -> None:
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
    csv_path = tmp_path / "sun.csv"
    csv_path.write_text(
        "time,intensity\n"
        "2026-07-22T12:00:00Z,1.0\n"
        "2026-07-22T12:00:01Z,1.2\n"
        "2026-07-22T12:00:02Z,3.5\n"
        "2026-07-22T12:00:03Z,1.1\n",
        encoding="utf-8",
    )
    product = ImportRadioTimeseries(archive, store).execute(
        workspace_id=ws.id,
        path=csv_path,
        site_id=site.id,
        frequency_mhz=1420.4,
    )
    assert product.product_type == "radio_timeseries"
    assert product.summary["n_points"] == 4
    assert product.summary["format"] == "csv"
    assert product.summary["power_max"] == 3.5
    archive.close()


def test_import_radio_bad_ext(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "bad.sqlite3")
    archive.migrate()
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    store = LocalArtifactStore(tmp_path / "art")
    bad = tmp_path / "x.wav"
    bad.write_bytes(b"RIFF")
    try:
        ImportRadioTimeseries(archive, store).execute(
            workspace_id=ws.id, path=bad
        )
        raise AssertionError("expected DomainError")
    except DomainError:
        pass
    archive.close()


def test_radio_builder() -> None:
    from astrocitizen.desktop.radio_panel import build_radio_dashboard

    assert callable(build_radio_dashboard)
