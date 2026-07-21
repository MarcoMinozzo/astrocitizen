"""Testes S2 — efemerides, meteo, ProgramaDiario."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from astrocitizen.adapters.meteo import ManualMeteo, OpenMeteo
from astrocitizen.adapters.sky import AstropyEphemeris
from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.adapters.sqlite.schema import SCHEMA_VERSION
from astrocitizen.inventory.models import Equipment, InstrumentConfig, Site
from astrocitizen.planning import GenerateDailyPlan, Target
from astrocitizen.planning.conflicts import resolve_priority_conflicts
from astrocitizen.planning.edit import EditDailyPlan
from astrocitizen.planning.meteo_rules import evaluate_meteo
from astrocitizen.planning.models import ObservationBlock
from astrocitizen.programs.models import Program
from astrocitizen.programs.seed import seed_program_templates
from astrocitizen.shared.ids import new_id
from astrocitizen.workspace.models import Workspace


def _setup(tmp_path: Path) -> tuple[SqliteArchive, Workspace, Site]:
    archive = SqliteArchive(tmp_path / "s2.sqlite3")
    assert archive.migrate() == SCHEMA_VERSION
    assert SCHEMA_VERSION == 2
    ws = archive.upsert_workspace(Workspace(id=new_id(), name="ws"))
    seed_program_templates(archive)
    site = archive.upsert_site(
        Site(
            id=new_id(),
            workspace_id=ws.id,
            name="TestSite",
            latitude_deg=-29.68,
            longitude_deg=-51.13,
            elevation_m=30.0,
            min_altitude_deg=15.0,
            is_default=True,
            meteo_thresholds={
                "max_cloud_cover_pct": 50,
                "max_wind_ms": 12,
                "max_humidity_pct": 90,
                "no_precipitation": True,
            },
        )
    )
    return archive, ws, site


def test_astropy_altaz_polaris_ish() -> None:
    eph = AstropyEphemeris()
    # Vega-ish coords; just ensure numeric output
    out = eph.altitude_azimuth(
        ra_deg=279.23,
        dec_deg=38.78,
        latitude_deg=40.0,
        longitude_deg=-74.0,
        elevation_m=10.0,
        utc_iso="2026-01-15T05:00:00Z",
    )
    assert "alt_deg" in out and "az_deg" in out
    assert isinstance(out["alt_deg"], float)


def test_night_window() -> None:
    eph = AstropyEphemeris()
    win = eph.night_window(
        latitude_deg=-30.0,
        longitude_deg=-51.0,
        elevation_m=0.0,
        night_date="2026-07-15",
    )
    assert win["start_utc"].endswith("Z")
    assert win["end_utc"].endswith("Z")
    assert win["start_utc"] < win["end_utc"]


def test_meteo_rules() -> None:
    ok, _ = evaluate_meteo({"cloud_cover_pct": 10, "wind_ms": 2, "humidity_pct": 40, "precipitation": False}, None)
    assert ok
    bad, reason = evaluate_meteo(
        {"cloud_cover_pct": 80, "wind_ms": 2, "humidity_pct": 40, "precipitation": False},
        {"max_cloud_cover_pct": 50},
    )
    assert not bad and reason and "nuvens" in reason


def test_open_meteo_mock() -> None:
    payload = b'{"current":{"cloud_cover":20,"wind_speed_10m":3.1,"relative_humidity_2m":55,"precipitation":0}}'

    class Resp:
        def read(self) -> bytes:
            return payload

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    with patch("astrocitizen.adapters.meteo.open_meteo.urlopen", return_value=Resp()):
        snap = OpenMeteo().snapshot(latitude_deg=-29.7, longitude_deg=-51.1)
    assert snap["source"] == "api"
    assert snap["cloud_cover_pct"] == 20.0


def test_generate_daily_plan_and_edit(tmp_path: Path) -> None:
    archive, ws, site = _setup(tmp_path)
    cam = archive.upsert_equipment(
        Equipment(id=new_id(), workspace_id=ws.id, type="camera", name="Cam", backend="sim")
    )
    mount = archive.upsert_equipment(
        Equipment(id=new_id(), workspace_id=ws.id, type="mount", name="Mount", backend="sim")
    )
    cfg = archive.upsert_instrument_config(
        InstrumentConfig(
            id=new_id(),
            workspace_id=ws.id,
            name="Setup",
            items={"camera": cam.id, "mount": mount.id},
        )
    )
    # High priority program
    p1 = archive.upsert_program(
        Program(
            id=new_id(),
            workspace_id=ws.id,
            template_id="PO-A01",
            name="Vars",
            state="active",
            priority=1,
            default_instrument_config_id=cfg.id,
        )
    )
    # Lower priority overlapping
    p2 = archive.upsert_program(
        Program(
            id=new_id(),
            workspace_id=ws.id,
            template_id="PO-A01",
            name="Other",
            state="active",
            priority=5,
            default_instrument_config_id=cfg.id,
        )
    )
    # Target near zenith-ish for southern site in July — use high southern dec
    t1 = archive.upsert_target(
        Target(
            id=new_id(),
            workspace_id=ws.id,
            designation="StarA",
            ra_deg=180.0,
            dec_deg=-30.0,
        )
    )
    t2 = archive.upsert_target(
        Target(
            id=new_id(),
            workspace_id=ws.id,
            designation="StarB",
            ra_deg=185.0,
            dec_deg=-32.0,
        )
    )
    archive.link_program_target(p1.id, t1.id)
    archive.link_program_target(p2.id, t2.id)

    plan = GenerateDailyPlan(archive, AstropyEphemeris(), ManualMeteo(cloud_cover_pct=5)).execute(
        workspace_id=ws.id,
        site_id=site.id,
        night_date="2026-07-15",
    )
    blocks = archive.list_observation_blocks(plan.id)
    assert len(blocks) == 2
    assert all(b.meteo_snapshot_id for b in blocks)

    # Force conflict resolution unit path
    b1 = ObservationBlock(
        id=new_id(),
        daily_plan_id=plan.id,
        window_start_utc="2026-07-16T00:00:00Z",
        window_end_utc="2026-07-16T04:00:00Z",
        status="agendado",
        priority=1,
        sort_order=0,
    )
    b2 = ObservationBlock(
        id=new_id(),
        daily_plan_id=plan.id,
        window_start_utc="2026-07-16T01:00:00Z",
        window_end_utc="2026-07-16T05:00:00Z",
        status="agendado",
        priority=9,
        sort_order=1,
    )
    resolve_priority_conflicts([b1, b2])
    assert b1.status == "agendado"
    assert b2.status == "candidato"

    # Edit
    victim = blocks[0]
    EditDailyPlan(archive).set_block_status(victim.id, "pulado", reason="manual skip")
    updated = archive.get_observation_block(victim.id)
    assert updated is not None
    assert updated.status == "pulado"
    archive.close()


def test_inviavel_meteo_and_equip(tmp_path: Path) -> None:
    archive, ws, site = _setup(tmp_path)
    # Program without instrument config -> inviavel_equip (if sky/meteo ok)
    p = archive.upsert_program(
        Program(
            id=new_id(),
            workspace_id=ws.id,
            template_id="PO-A01",
            name="NoEquip",
            state="active",
            priority=1,
        )
    )
    t = archive.upsert_target(
        Target(id=new_id(), workspace_id=ws.id, designation="T", ra_deg=180.0, dec_deg=-30.0)
    )
    archive.link_program_target(p.id, t.id)

    # Bad meteo first
    plan = GenerateDailyPlan(
        archive, AstropyEphemeris(), ManualMeteo(cloud_cover_pct=90)
    ).execute(workspace_id=ws.id, site_id=site.id, night_date="2026-07-20")
    blocks = archive.list_observation_blocks(plan.id)
    assert blocks
    # Either inviavel_ceu or inviavel_meteo depending on altitude
    assert blocks[0].status in ("inviavel_meteo", "inviavel_ceu", "inviavel_equip")
    archive.close()


def test_schema_v2_tables_exist(tmp_path: Path) -> None:
    archive, _, _ = _setup(tmp_path)
    rows = archive._conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    names = {r[0] for r in rows}
    for t in (
        "targets",
        "program_targets",
        "daily_plans",
        "observation_blocks",
        "meteo_snapshots",
        "ephemeris_snapshots",
    ):
        assert t in names
    archive.close()
