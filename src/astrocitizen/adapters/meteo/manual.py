"""MeteoPort manual (RN-023) — current + forecast sintetico."""

from __future__ import annotations

from typing import Any


class ManualMeteo:
    """Snapshot / forecast meteo fornecido pelo observador."""

    def __init__(
        self,
        *,
        cloud_cover_pct: float = 0.0,
        wind_ms: float = 0.0,
        humidity_pct: float = 50.0,
        precipitation: bool = False,
        temperature_c: float = 15.0,
        dewpoint_c: float = 5.0,
        precip_probability_pct: float = 0.0,
    ) -> None:
        self._base = {
            "cloud_cover_pct": cloud_cover_pct,
            "wind_ms": wind_ms,
            "humidity_pct": humidity_pct,
            "precipitation": precipitation,
            "precipitation_mm": 1.0 if precipitation else 0.0,
            "precip_probability_pct": precip_probability_pct,
            "temperature_c": temperature_c,
            "dewpoint_c": dewpoint_c,
            "dew_margin_c": temperature_c - dewpoint_c,
            "source": "manual",
            "provider": "manual",
        }

    def snapshot(
        self,
        *,
        latitude_deg: float,
        longitude_deg: float,
        elevation_m: float | None = None,
    ) -> dict[str, Any]:
        _ = elevation_m
        out = dict(self._base)
        out["latitude_deg"] = latitude_deg
        out["longitude_deg"] = longitude_deg
        out["request_latitude_deg"] = latitude_deg
        out["request_longitude_deg"] = longitude_deg
        return out

    def forecast(
        self,
        *,
        latitude_deg: float,
        longitude_deg: float,
        start_utc: str | None = None,
        end_utc: str | None = None,
        elevation_m: float | None = None,
    ) -> dict[str, Any]:
        out = self.snapshot(
            latitude_deg=latitude_deg,
            longitude_deg=longitude_deg,
            elevation_m=elevation_m,
        )
        hour = {
            "time_utc": start_utc or "manual",
            "cloud_cover_pct": self._base["cloud_cover_pct"],
            "cloud_cover_low_pct": self._base["cloud_cover_pct"],
            "cloud_cover_mid_pct": 0.0,
            "cloud_cover_high_pct": 0.0,
            "wind_ms": self._base["wind_ms"],
            "humidity_pct": self._base["humidity_pct"],
            "temperature_c": self._base["temperature_c"],
            "dewpoint_c": self._base["dewpoint_c"],
            "precipitation": self._base["precipitation"],
            "precipitation_mm": self._base["precipitation_mm"],
            "precip_probability_pct": self._base["precip_probability_pct"],
        }
        out["hourly"] = [hour]
        out["window_start_utc"] = start_utc
        out["window_end_utc"] = end_utc
        return out
