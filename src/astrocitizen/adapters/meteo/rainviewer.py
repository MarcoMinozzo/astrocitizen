"""RadarPort via RainViewer (imagem centrada no Site)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from astrocitizen.shared.errors import DomainError
from astrocitizen.shared.timeutil import utc_now_iso

MAPS_URL = "https://api.rainviewer.com/public/weather-maps.json"


class RainViewerRadar:
    """Descarrega PNG de radar composto centrado em lat/lon.

    Uso pessoal/educacional; atribuir https://www.rainviewer.com/ na UI.
    """

    def __init__(self, *, timeout_s: float = 20.0) -> None:
        self.timeout_s = timeout_s

    def _get_json(self, url: str) -> dict[str, Any]:
        req = Request(url, headers={"User-Agent": "astrocitizen/0.0.1"})
        try:
            with urlopen(req, timeout=self.timeout_s) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            raise DomainError(f"radar API indisponivel: {exc}") from exc

    def _get_bytes(self, url: str) -> bytes:
        req = Request(url, headers={"User-Agent": "astrocitizen/0.0.1"})
        try:
            with urlopen(req, timeout=self.timeout_s) as resp:
                return resp.read()
        except (URLError, TimeoutError, OSError) as exc:
            raise DomainError(f"radar download falhou: {exc}") from exc

    def region_image(
        self,
        *,
        latitude_deg: float,
        longitude_deg: float,
        zoom: int = 6,
        size: int = 512,
        out_path: Path | None = None,
        color: int = 2,
        smooth: int = 1,
        snow: int = 1,
    ) -> dict[str, Any]:
        meta = self._get_json(MAPS_URL)
        host = str(meta.get("host") or "").rstrip("/")
        past = (meta.get("radar") or {}).get("past") or []
        if not host or not past:
            raise DomainError("RainViewer sem frames de radar disponiveis")
        frame = past[-1]
        path = frame.get("path")
        ts = frame.get("time")
        # Free tier: lat/lon centered PNG
        # {host}/v2/radar/{path}/{size}/{z}/{lat}/{lon}/{color}/{smooth}_{snow}.png
        z = max(0, min(int(zoom), 7))
        sz = 512 if size >= 512 else 256
        url = (
            f"{host}{path}/{sz}/{z}/{latitude_deg:.4f}/{longitude_deg:.4f}/"
            f"{color}/{smooth}_{snow}.png"
        )
        png = self._get_bytes(url)
        dest = Path(out_path) if out_path else Path(f"/tmp/astrocitizen_radar_{ts}.png")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(png)
        return {
            "provider": "rainviewer",
            "source": "radar",
            "image_path": str(dest.resolve()),
            "image_url": url,
            "radar_time": ts,
            "captured_at_utc": utc_now_iso(),
            "latitude_deg": latitude_deg,
            "longitude_deg": longitude_deg,
            "zoom": z,
            "size": sz,
            "bytes": len(png),
            "attribution": "Radar data by RainViewer (https://www.rainviewer.com/)",
        }
