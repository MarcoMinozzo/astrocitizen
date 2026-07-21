"""Simuladores de hardware (sem dispositivo fisico)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from astropy.io import fits

from astrocitizen.shared.errors import DomainError
from astrocitizen.shared.timeutil import utc_now_iso


class SimulatorCamera:
    """CameraPort simulada — gera FITS sintetico."""

    backend_name = "sim"

    def __init__(self, *, width: int = 64, height: int = 64) -> None:
        self.width = width
        self.height = height
        self._connected = False
        self._last_data: np.ndarray | None = None
        self._last_meta: dict[str, Any] = {}

    def connect(self, device: str = "usb") -> None:
        self._connected = True
        self._device = device

    def disconnect(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def expose(
        self,
        *,
        exptime_s: float,
        frame_type: str = "light",
        binning: int = 1,
    ) -> dict[str, Any]:
        if not self._connected:
            raise DomainError("camera nao ligada", rule_id="RN-092")
        rng = np.random.default_rng(int(exptime_s * 1000) % 2**31)
        base = 1000.0 if frame_type == "light" else 100.0
        self._last_data = (
            base + rng.normal(0, 5, size=(self.height, self.width))
        ).astype(np.float32)
        self._last_meta = {
            "EXPTIME": float(exptime_s),
            "IMAGETYP": frame_type.upper(),
            "BINNING": int(binning),
            "XPIXSZ": 9.0,
            "YPIXSZ": 9.0,
            "DATE-OBS": utc_now_iso(),
            "INSTRUME": "SimulatorCamera",
        }
        return dict(self._last_meta)

    def save_fits(self, path: Path, *, headers: dict[str, Any] | None = None) -> Path:
        if self._last_data is None:
            raise DomainError("nenhuma exposicao para gravar")
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        hdu = fits.PrimaryHDU(self._last_data)
        hdr = hdu.header
        for k, v in {**self._last_meta, **(headers or {})}.items():
            key = str(k)[:8].upper()
            try:
                hdr[key] = v
            except (ValueError, TypeError):
                hdr[key] = str(v)
        hdu.writeto(path, overwrite=False)
        return path


class SimulatorMount:
    """MountPort simulada."""

    backend_name = "sim"

    def __init__(self) -> None:
        self._connected = False
        self._ra = 0.0
        self._dec = 0.0

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def slew_radec(self, ra_deg: float, dec_deg: float) -> None:
        if not self._connected:
            raise DomainError("montagem nao ligada", rule_id="RN-092")
        self._ra = float(ra_deg)
        self._dec = float(dec_deg)

    def get_radec(self) -> tuple[float, float]:
        return self._ra, self._dec


class SimulatorFocuser:
    """FocuserPort simulada."""

    backend_name = "sim"

    def __init__(self) -> None:
        self._connected = False
        self._position = 10000

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def move(self, position: int) -> None:
        if not self._connected:
            raise DomainError("focuser nao ligado", rule_id="RN-092")
        self._position = int(position)

    def get_position(self) -> int:
        return self._position
