"""Testes do painel Noite (helpers sem GUI)."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

from astrocitizen.desktop.night import (
    fetch_plan_status,
    forecast_summary_lines,
    hourly_table_rows,
    plan_status_text,
    tonight_utc_date,
)


def test_tonight_utc_date_format() -> None:
    d = tonight_utc_date()
    assert len(d) == 10 and d[4] == "-" and d[7] == "-"


def test_forecast_summary_and_hours() -> None:
    fc = {
        "cloud_cover_pct": 80,
        "wind_ms": 3.2,
        "humidity_pct": 70,
        "dew_margin_c": 1.5,
        "precipitation": True,
        "precip_probability_pct": 60,
        "hourly": [
            {
                "time_utc": "2026-07-21T23:00",
                "cloud_cover_pct": 80,
                "wind_ms": 3.2,
                "humidity_pct": 70,
                "dewpoint_c": 10,
                "precipitation_mm": 0.5,
                "precip_probability_pct": 60,
            }
        ],
    }
    lines = forecast_summary_lines(
        fc,
        ok=False,
        reason="nuvens",
        night_start="2026-07-21T22:00:00Z",
        night_end="2026-07-22T09:00:00Z",
    )
    assert "INVIABLE" in lines[0]
    assert any("reason=nuvens" in x for x in lines)
    rows = hourly_table_rows(fc)
    assert rows[0][0] == "2026-07-21T23:00"
    assert rows[0][1] == "80"


def test_plan_status_text() -> None:
    assert "nenhum gerado" in plan_status_text(None, [])
    plan = SimpleNamespace(id="12345678-aaaa-bbbb-cccc-ddddeeeeffff", state="draft")
    blocks = [
        SimpleNamespace(status="ok"),
        SimpleNamespace(status="inviavel_meteo"),
        SimpleNamespace(status="ok"),
    ]
    text = plan_status_text(plan, blocks)
    assert "plano=draft" in text
    assert "ok=2" in text
    assert "inviavel_meteo=1" in text


def test_fetch_plan_status_empty() -> None:
    class Arch:
        def get_daily_plan_for_night(self, *a, **k):
            return None

        def list_observation_blocks(self, *a, **k):
            return []

    msg = fetch_plan_status(Arch(), uuid4(), uuid4(), "2026-07-21")
    assert "nenhum gerado" in msg
