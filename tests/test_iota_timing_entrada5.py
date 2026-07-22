"""IOTA IN-PRED + timing + video/LC (ENTRADA #5 close)."""

from __future__ import annotations

from pathlib import Path

from astrocitizen.adapters.fs import LocalArtifactStore
from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.inventory.models import Site
from astrocitizen.observatory import (
    ImportIotaPrediction,
    RegisterOccultationTiming,
    parse_iota_prediction_text,
    parse_occultation_lc_csv,
    suggest_contacts_from_lc,
)
from astrocitizen.shared.errors import DomainError
from astrocitizen.shared.ids import new_id
from astrocitizen.workspace.models import Workspace


def test_parse_txt_prediction() -> None:
    text = """
#TYPE=ASTROCITIZEN_IOTA_PRED
EventID: 2026Jul22_Demo
Star: TYC 1234-5678-1
Asteroid: (704) Interamnia
EventUTC: 2026-07-22T03:15:00Z
Duration_s: 12.5
"""
    p = parse_iota_prediction_text(text)
    assert p["event_id"] == "2026Jul22_Demo"
    assert "Interamnia" in p["asteroid"]
    assert p["duration_s"] == 12.5


def test_parse_csv_prediction() -> None:
    text = "event_id,star,asteroid,event_utc,duration_s\nE1,StarA,AstB,2026-07-22T01:00:00Z,8\n"
    p = parse_iota_prediction_text(text)
    assert p["event_id"] == "E1"
    assert p["star"] == "StarA"
    assert p["source_format"] == "csv"


def test_parse_lc_and_suggest(tmp_path: Path) -> None:
    lc = tmp_path / "lc.csv"
    rows = ["t_utc,signal"]
    for i in range(10):
        t = f"2026-07-22T04:00:{i:02d}Z"
        y = 100.0 if i < 3 or i > 6 else 20.0
        rows.append(f"{t},{y}")
    lc.write_text("\n".join(rows) + "\n", encoding="utf-8")
    pts = parse_occultation_lc_csv(lc)
    assert len(pts) == 10
    sug = suggest_contacts_from_lc(pts)
    assert sug["d_time_utc"] is not None
    assert sug["r_time_utc"] is not None


def test_import_and_register(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "i.sqlite3")
    archive.migrate()
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    site = archive.upsert_site(
        Site(
            id=new_id(),
            workspace_id=ws.id,
            name="Casa",
            latitude_deg=-29.0,
            longitude_deg=-51.0,
        )
    )
    pred_file = tmp_path / "pred.txt"
    pred_file.write_text(
        "EventID: EV99\nStar: HIP 123\nAsteroid: (1) Ceres\nEventUTC: 2026-07-22T04:00:00Z\n",
        encoding="utf-8",
    )
    store = LocalArtifactStore(tmp_path / "art")
    pred = ImportIotaPrediction(archive, store).execute(
        workspace_id=ws.id, path=pred_file, site_id=site.id
    )
    assert pred.product_type == "occultation_prediction"
    assert pred.summary["event_id"] == "EV99"

    timing = RegisterOccultationTiming(archive).execute(
        workspace_id=ws.id,
        event_id="EV99",
        star="HIP 123",
        asteroid="(1) Ceres",
        result="positive",
        d_time_utc="2026-07-22T04:00:10Z",
        r_time_utc="2026-07-22T04:00:22Z",
        site_id=site.id,
        prediction_product_id=pred.id,
    )
    assert timing.product_type == "occultation_timing"
    assert timing.summary["result"] == "positive"

    try:
        RegisterOccultationTiming(archive).execute(
            workspace_id=ws.id,
            event_id="X",
            star="S",
            asteroid="A",
            result="positive",
        )
        raise AssertionError("expected DomainError")
    except DomainError:
        pass
    archive.close()


def test_register_with_video_and_lc(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "v.sqlite3")
    archive.migrate()
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    store = LocalArtifactStore(tmp_path / "art")

    video = tmp_path / "event.ser"
    video.write_bytes(b"SERFAKE")
    lc = tmp_path / "lc.csv"
    lc.write_text(
        "t_utc,signal\n"
        "2026-07-22T04:00:00Z,100\n"
        "2026-07-22T04:00:01Z,100\n"
        "2026-07-22T04:00:02Z,20\n"
        "2026-07-22T04:00:03Z,20\n"
        "2026-07-22T04:00:04Z,100\n"
        "2026-07-22T04:00:05Z,100\n",
        encoding="utf-8",
    )

    timing = RegisterOccultationTiming(archive, store).execute(
        workspace_id=ws.id,
        event_id="EVVID",
        star="Star",
        asteroid="Ast",
        result="positive",
        timesource="GPS",
        video_path=video,
        lc_csv_path=lc,
        suggest_contacts=True,
    )
    assert timing.summary["has_video"] is True
    assert timing.summary["n_lc_points"] == 6
    assert timing.summary["timesource"] == "GPS"
    assert timing.summary["d_time_utc"]
    assert timing.summary["r_time_utc"]
    archive.close()


def test_timing_builder() -> None:
    from astrocitizen.desktop.timing_panel import build_timing_dashboard

    assert callable(build_timing_dashboard)
