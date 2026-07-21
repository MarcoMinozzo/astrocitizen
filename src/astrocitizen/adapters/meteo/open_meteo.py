"""MeteoPort via Open-Meteo (sem API key)."""

from __future__ import annotations

import json
from typing import Any
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from astrocitizen.shared.errors import DomainError

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


class OpenMeteo:
    """Consulta condicoes actuais no local do Site (RN-024)."""

    def __init__(self, *, timeout_s: float = 15.0) -> None:
        self.timeout_s = timeout_s

    def snapshot(self, *, latitude_deg: float, longitude_deg: float) -> dict[str, Any]:
        params = urlencode(
            {
                "latitude": latitude_deg,
                "longitude": longitude_deg,
                "current": "cloud_cover,wind_speed_10m,relative_humidity_2m,precipitation",
                "wind_speed_unit": "ms",
                "timezone": "UTC",
            }
        )
        url = f"{OPEN_METEO_URL}?{params}"
        req = Request(url, headers={"User-Agent": "astrocitizen/0.0.1"})
        try:
            with urlopen(req, timeout=self.timeout_s) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except (URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            raise DomainError(f"meteo API indisponivel: {exc}", rule_id="RN-023") from exc

        current = data.get("current") or {}
        precip = float(current.get("precipitation") or 0.0)
        return {
            "cloud_cover_pct": float(current.get("cloud_cover") or 0.0),
            "wind_ms": float(current.get("wind_speed_10m") or 0.0),
            "humidity_pct": float(current.get("relative_humidity_2m") or 0.0),
            "precipitation": precip > 0.0,
            "precipitation_mm": precip,
            "source": "api",
            "provider": "open-meteo",
            "latitude_deg": latitude_deg,
            "longitude_deg": longitude_deg,
            "raw_current": current,
        }
