"""MeteoPort manual (RN-023)."""

from __future__ import annotations

from typing import Any


class ManualMeteo:
    """Snapshot meteo fornecido pelo observador."""

    def __init__(
        self,
        *,
        cloud_cover_pct: float = 0.0,
        wind_ms: float = 0.0,
        humidity_pct: float = 50.0,
        precipitation: bool = False,
    ) -> None:
        self._payload = {
            "cloud_cover_pct": cloud_cover_pct,
            "wind_ms": wind_ms,
            "humidity_pct": humidity_pct,
            "precipitation": precipitation,
            "source": "manual",
        }

    def snapshot(self, *, latitude_deg: float, longitude_deg: float) -> dict[str, Any]:
        out = dict(self._payload)
        out["latitude_deg"] = latitude_deg
        out["longitude_deg"] = longitude_deg
        return out
