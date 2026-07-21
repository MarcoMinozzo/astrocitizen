"""Avaliacao de limiares meteo do Site (RN-021)."""

from __future__ import annotations

from typing import Any


DEFAULT_THRESHOLDS = {
    "max_cloud_cover_pct": 50.0,
    "max_wind_ms": 12.0,
    "max_humidity_pct": 90.0,
    "no_precipitation": True,
    "max_precip_probability_pct": 40.0,
    "min_dew_margin_c": 2.0,
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
    precip_prob = payload.get("precip_probability_pct")
    dew_margin = payload.get("dew_margin_c")
    if dew_margin is None:
        t = payload.get("temperature_c")
        d = payload.get("dewpoint_c")
        if t is not None and d is not None:
            dew_margin = float(t) - float(d)

    if cloud > float(thr["max_cloud_cover_pct"]):
        return False, f"nuvens {cloud:.0f}% > limiar {thr['max_cloud_cover_pct']}%"
    if wind > float(thr["max_wind_ms"]):
        return False, f"vento {wind:.1f} m/s > limiar {thr['max_wind_ms']} m/s"
    if humidity > float(thr["max_humidity_pct"]):
        return False, f"humidade {humidity:.0f}% > limiar {thr['max_humidity_pct']}%"
    if thr.get("no_precipitation") and precip:
        return False, "precipitacao prevista/actual"
    if precip_prob is not None and float(precip_prob) > float(thr["max_precip_probability_pct"]):
        return (
            False,
            f"prob. precip {float(precip_prob):.0f}% > limiar {thr['max_precip_probability_pct']}%",
        )
    if dew_margin is not None and float(dew_margin) < float(thr["min_dew_margin_c"]):
        return (
            False,
            f"margem orvalho {float(dew_margin):.1f} C < limiar {thr['min_dew_margin_c']} C",
        )
    return True, None


def evaluate_meteo_window(
    forecast: dict[str, Any],
    thresholds: dict[str, Any] | None,
) -> tuple[bool, str | None]:
    """Avalia resumo da janela (pior caso) ou cada hora se hourly presente."""
    hours = forecast.get("hourly") or []
    if not hours:
        return evaluate_meteo(forecast, thresholds)
    # Usa o proprio resumo do forecast (OpenMeteo ja agrega pior caso)
    ok, reason = evaluate_meteo(forecast, thresholds)
    if not ok:
        return ok, reason
    # Dupla verificacao hora a hora (motivos mais especificos)
    for h in hours:
        ok_h, reason_h = evaluate_meteo(h, thresholds)
        if not ok_h:
            when = h.get("time_utc") or "?"
            return False, f"{when}: {reason_h}"
    return True, None
