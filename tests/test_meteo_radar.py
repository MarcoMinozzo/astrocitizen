"""Testes meteo hourly + radar RainViewer."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from astrocitizen.adapters.meteo import ManualMeteo, OpenMeteo, RainViewerRadar
from astrocitizen.planning.meteo_rules import evaluate_meteo, evaluate_meteo_window


class _Resp:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_evaluate_dew_and_precip_prob() -> None:
    ok, _ = evaluate_meteo(
        {
            "cloud_cover_pct": 10,
            "wind_ms": 2,
            "humidity_pct": 40,
            "precipitation": False,
            "precip_probability_pct": 10,
            "temperature_c": 15,
            "dewpoint_c": 5,
        },
        None,
    )
    assert ok
    bad, reason = evaluate_meteo(
        {
            "cloud_cover_pct": 10,
            "wind_ms": 2,
            "humidity_pct": 40,
            "precipitation": False,
            "temperature_c": 10,
            "dewpoint_c": 9.5,
        },
        {"min_dew_margin_c": 2.0},
    )
    assert not bad and reason and "orvalho" in reason


def test_evaluate_meteo_window_picks_worst_hour() -> None:
    fc = {
        "cloud_cover_pct": 80,
        "wind_ms": 2,
        "humidity_pct": 40,
        "precipitation": False,
        "hourly": [
            {
                "time_utc": "2026-07-21T22:00",
                "cloud_cover_pct": 10,
                "wind_ms": 2,
                "humidity_pct": 40,
                "precipitation": False,
                "temperature_c": 15,
                "dewpoint_c": 5,
            },
            {
                "time_utc": "2026-07-22T02:00",
                "cloud_cover_pct": 90,
                "wind_ms": 2,
                "humidity_pct": 40,
                "precipitation": False,
                "temperature_c": 15,
                "dewpoint_c": 5,
            },
        ],
    }
    ok, reason = evaluate_meteo_window(fc, {"max_cloud_cover_pct": 50})
    assert not ok
    assert reason is not None


def test_open_meteo_forecast_mock() -> None:
    payload = {
        "current": {
            "temperature_2m": 18.0,
            "relative_humidity_2m": 55,
            "dew_point_2m": 8.0,
            "precipitation": 0,
            "cloud_cover": 20,
            "wind_speed_10m": 3.1,
        },
        "hourly": {
            "time": ["2026-07-21T22:00", "2026-07-22T01:00", "2026-07-22T10:00"],
            "temperature_2m": [18.0, 16.0, 20.0],
            "relative_humidity_2m": [55, 60, 50],
            "dew_point_2m": [8.0, 9.0, 7.0],
            "precipitation": [0.0, 0.0, 0.0],
            "precipitation_probability": [5, 10, 0],
            "cloud_cover": [20, 35, 10],
            "cloud_cover_low": [10, 20, 5],
            "cloud_cover_mid": [5, 10, 0],
            "cloud_cover_high": [5, 5, 5],
            "wind_speed_10m": [3.0, 4.0, 2.0],
        },
    }
    with patch(
        "astrocitizen.adapters.meteo.open_meteo.urlopen",
        return_value=_Resp(json.dumps(payload).encode()),
    ):
        fc = OpenMeteo().forecast(
            latitude_deg=-29.7,
            longitude_deg=-51.1,
            start_utc="2026-07-21T21:00:00Z",
            end_utc="2026-07-22T05:00:00Z",
        )
    assert fc["provider"] == "open-meteo"
    assert len(fc["hourly"]) == 2  # 10:00 filtered out
    assert fc["cloud_cover_pct"] == 35.0
    assert fc["dew_margin_c"] is not None


def test_manual_forecast() -> None:
    fc = ManualMeteo(cloud_cover_pct=12).forecast(
        latitude_deg=0, longitude_deg=0, start_utc="2026-01-01T00:00:00Z"
    )
    assert fc["hourly"][0]["cloud_cover_pct"] == 12


def test_rainviewer_region_image(tmp_path: Path) -> None:
    maps = {
        "host": "https://tilecache.example",
        "radar": {"past": [{"time": 1700000000, "path": "/v2/radar/1700000000"}]},
    }
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
    out = tmp_path / "radar.png"

    def fake_urlopen(req, timeout=0):  # noqa: ARG001
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "weather-maps.json" in url:
            return _Resp(json.dumps(maps).encode())
        return _Resp(png)

    with patch("astrocitizen.adapters.meteo.rainviewer.urlopen", side_effect=fake_urlopen):
        meta = RainViewerRadar().region_image(
            latitude_deg=-29.68,
            longitude_deg=-51.13,
            zoom=5,
            out_path=out,
        )
    assert out.exists()
    assert meta["provider"] == "rainviewer"
    assert meta["bytes"] == len(png)
    assert "RainViewer" in meta["attribution"]
