"""MeteoPort via Open-Meteo (sem API key) — current + hourly."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from astrocitizen.shared.errors import DomainError

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

HOURLY_VARS = (
    "temperature_2m,relative_humidity_2m,dew_point_2m,"
    "precipitation,precipitation_probability,"
    "cloud_cover,cloud_cover_low,cloud_cover_mid,cloud_cover_high,"
    "wind_speed_10m"
)

CURRENT_VARS = (
    "temperature_2m,relative_humidity_2m,dew_point_2m,"
    "precipitation,cloud_cover,wind_speed_10m"
)


def _parse_utc(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(timezone.utc)


def forecast_days_for_window(
    start_utc: str | None,
    end_utc: str | None,
    *,
    now: datetime | None = None,
) -> int:
    """Dias de forecast Open-Meteo (1..16) para cobrir a janela da noite."""
    now = now or datetime.now(timezone.utc)
    end = _parse_utc(end_utc) if end_utc else now
    start = _parse_utc(start_utc) if start_utc else now
    last = max(end, start, now)
    days = (last.date() - now.date()).days + 1
    return max(1, min(16, int(days)))


def _row_from_current(current: dict[str, Any], *, lat: float, lon: float) -> dict[str, Any]:
    precip = float(current.get("precipitation") or 0.0)
    return {
        "cloud_cover_pct": float(current.get("cloud_cover") or 0.0),
        "wind_ms": float(current.get("wind_speed_10m") or 0.0),
        "humidity_pct": float(current.get("relative_humidity_2m") or 0.0),
        "temperature_c": float(current.get("temperature_2m") or 0.0)
        if current.get("temperature_2m") is not None
        else None,
        "dewpoint_c": float(current.get("dew_point_2m") or 0.0)
        if current.get("dew_point_2m") is not None
        else None,
        "precipitation": precip > 0.0,
        "precipitation_mm": precip,
        "precip_probability_pct": None,
        "source": "api",
        "provider": "open-meteo",
        "latitude_deg": lat,
        "longitude_deg": lon,
        "raw_current": current,
    }


def _hour_row(hourly: dict[str, Any], idx: int) -> dict[str, Any]:
    precip = float((hourly.get("precipitation") or [0])[idx] or 0.0)
    prob = hourly.get("precipitation_probability")
    return {
        "time_utc": (hourly.get("time") or [None])[idx],
        "cloud_cover_pct": float((hourly.get("cloud_cover") or [0])[idx] or 0.0),
        "cloud_cover_low_pct": float((hourly.get("cloud_cover_low") or [0])[idx] or 0.0),
        "cloud_cover_mid_pct": float((hourly.get("cloud_cover_mid") or [0])[idx] or 0.0),
        "cloud_cover_high_pct": float((hourly.get("cloud_cover_high") or [0])[idx] or 0.0),
        "wind_ms": float((hourly.get("wind_speed_10m") or [0])[idx] or 0.0),
        "humidity_pct": float((hourly.get("relative_humidity_2m") or [0])[idx] or 0.0),
        "temperature_c": float((hourly.get("temperature_2m") or [0])[idx] or 0.0),
        "dewpoint_c": float((hourly.get("dew_point_2m") or [0])[idx] or 0.0),
        "precipitation": precip > 0.05,
        "precipitation_mm": precip,
        "precip_probability_pct": float(prob[idx]) if prob and prob[idx] is not None else None,
    }


class OpenMeteo:
    """Forecast Open-Meteo no lat/lon do Site (RN-024)."""

    def __init__(self, *, timeout_s: float = 20.0, forecast_days: int | None = None) -> None:
        self.timeout_s = timeout_s
        # None = calcular a partir da janela; senao fixo (testes / override)
        self.forecast_days = forecast_days

    def _get(self, params: dict[str, Any]) -> dict[str, Any]:
        url = f"{OPEN_METEO_URL}?{urlencode(params)}"
        req = Request(url, headers={"User-Agent": "astrocitizen/0.0.1"})
        try:
            with urlopen(req, timeout=self.timeout_s) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            raise DomainError(f"meteo API indisponivel: {exc}", rule_id="RN-023") from exc

    def snapshot(
        self,
        *,
        latitude_deg: float,
        longitude_deg: float,
        elevation_m: float | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "latitude": latitude_deg,
            "longitude": longitude_deg,
            "current": CURRENT_VARS,
            "wind_speed_unit": "ms",
            "timezone": "UTC",
        }
        if elevation_m is not None:
            params["elevation"] = elevation_m
        data = self._get(params)
        out = _row_from_current(
            data.get("current") or {}, lat=latitude_deg, lon=longitude_deg
        )
        if "latitude" in data:
            out["api_latitude_deg"] = float(data["latitude"])
        if "longitude" in data:
            out["api_longitude_deg"] = float(data["longitude"])
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
        days = (
            int(self.forecast_days)
            if self.forecast_days is not None
            else forecast_days_for_window(start_utc, end_utc)
        )
        params: dict[str, Any] = {
            "latitude": latitude_deg,
            "longitude": longitude_deg,
            "current": CURRENT_VARS,
            "hourly": HOURLY_VARS,
            "forecast_days": days,
            "wind_speed_unit": "ms",
            "timezone": "UTC",
        }
        if elevation_m is not None:
            params["elevation"] = elevation_m
        data = self._get(params)
        out = _row_from_current(
            data.get("current") or {}, lat=latitude_deg, lon=longitude_deg
        )
        out["request_latitude_deg"] = float(latitude_deg)
        out["request_longitude_deg"] = float(longitude_deg)
        if "latitude" in data:
            out["api_latitude_deg"] = float(data["latitude"])
        if "longitude" in data:
            out["api_longitude_deg"] = float(data["longitude"])
        out["forecast_days"] = days
        hourly = data.get("hourly") or {}
        times = hourly.get("time") or []
        rows: list[dict[str, Any]] = []
        t0 = _parse_utc(start_utc) if start_utc else None
        t1 = _parse_utc(end_utc) if end_utc else None
        for i, t in enumerate(times):
            # Open-Meteo hourly times are like 2026-07-21T00:00
            ts = _parse_utc(t if t.endswith("Z") else t + "Z")
            if t0 and ts < t0:
                continue
            if t1 and ts > t1:
                continue
            rows.append(_hour_row(hourly, i))
        out["hourly"] = rows
        out["window_start_utc"] = start_utc
        out["window_end_utc"] = end_utc
        if rows:
            # Resumo pior caso na janela (para limiares do plano)
            out["cloud_cover_pct"] = max(r["cloud_cover_pct"] for r in rows)
            out["wind_ms"] = max(r["wind_ms"] for r in rows)
            out["humidity_pct"] = max(r["humidity_pct"] for r in rows)
            out["precipitation"] = any(r["precipitation"] for r in rows)
            out["precipitation_mm"] = max(r["precipitation_mm"] for r in rows)
            probs = [
                r["precip_probability_pct"]
                for r in rows
                if r["precip_probability_pct"] is not None
            ]
            out["precip_probability_pct"] = max(probs) if probs else None
            # dew margin: min (temp - dewpoint)
            margins = [
                r["temperature_c"] - r["dewpoint_c"]
                for r in rows
                if r.get("temperature_c") is not None and r.get("dewpoint_c") is not None
            ]
            out["dew_margin_c"] = min(margins) if margins else None
            out["temperature_c"] = min(r["temperature_c"] for r in rows)
            out["dewpoint_c"] = max(r["dewpoint_c"] for r in rows)
        return out
