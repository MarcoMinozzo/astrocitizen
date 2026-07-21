"""Avaliacao de limiares meteo do Site (RN-021)."""

from __future__ import annotations

from typing import Any


DEFAULT_THRESHOLDS = {
    "max_cloud_cover_pct": 50.0,
    "max_wind_ms": 12.0,
    "max_humidity_pct": 90.0,
    "no_precipitation": True,
}


def evaluate_meteo(
    payload: dict[str, Any],
    thresholds: dict[str, Any] | None,
) -> tuple[bool, str | None]:
    """Retorna (ok, motivo). ok=False => inviavel_meteo."""
    thr = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    cloud = float(payload.get("cloud_cover_pct") or 0.0)
    wind = float(payload.get("wind_ms") or 0.0)
    humidity = float(payload.get("humidity_pct") or 0.0)
    precip = bool(payload.get("precipitation"))

    if cloud > float(thr["max_cloud_cover_pct"]):
        return False, f"nuvens {cloud:.0f}% > limiar {thr['max_cloud_cover_pct']}%"
    if wind > float(thr["max_wind_ms"]):
        return False, f"vento {wind:.1f} m/s > limiar {thr['max_wind_ms']} m/s"
    if humidity > float(thr["max_humidity_pct"]):
        return False, f"humidade {humidity:.0f}% > limiar {thr['max_humidity_pct']}%"
    if thr.get("no_precipitation") and precip:
        return False, "precipitacao prevista/actual"
    return True, None
