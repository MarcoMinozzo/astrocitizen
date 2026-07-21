"""Stubs Alpaca / udrv — requerem extras; S3 expoe API sem hardware real."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from astrocitizen.shared.errors import DomainError


def _need(pkg: str, feature: str) -> DomainError:
    return DomainError(
        f"{feature} requer '{pkg}' (pip install 'astrocitizen[alpaca]') "
        "e servidor Alpaca/Omni Simulator; use backend=sim em desenvolvimento",
        rule_id="AC-041",
    )


class AlpacaCamera:
    backend_name = "alpaca"

    def __init__(self, *, host: str = "127.0.0.1", port: int = 11111, **_: Any) -> None:
        self.host = host
        self.port = port
        self._connected = False

    def connect(self, device: str = "usb") -> None:
        try:
            import alpyca  # noqa: F401
        except ImportError as exc:
            raise _need("alpyca", "Alpaca Camera") from exc
        raise DomainError(
            "AlpacaCamera: ligacao real ao Omni Simulator fica para AC-047/S4; use sim",
            rule_id="AC-041",
        )

    def disconnect(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def expose(self, *, exptime_s: float, frame_type: str = "light", binning: int = 1) -> dict:
        raise DomainError("AlpacaCamera nao ligada", rule_id="RN-092")

    def save_fits(self, path: Path, *, headers: dict[str, Any] | None = None) -> Path:
        raise DomainError("AlpacaCamera nao ligada", rule_id="RN-092")


class AlpacaMount:
    backend_name = "alpaca"

    def __init__(self, *, host: str = "127.0.0.1", port: int = 11111, **_: Any) -> None:
        self.host = host
        self.port = port
        self._connected = False

    def connect(self) -> None:
        try:
            import alpyca  # noqa: F401
        except ImportError as exc:
            raise _need("alpyca", "Alpaca Mount") from exc
        raise DomainError("AlpacaMount: use backend=sim ate Omni Simulator", rule_id="AC-043")

    def disconnect(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def slew_radec(self, ra_deg: float, dec_deg: float) -> None:
        raise DomainError("montagem nao ligada", rule_id="RN-092")

    def get_radec(self) -> tuple[float, float]:
        return 0.0, 0.0


class AlpacaFocuser:
    backend_name = "alpaca"

    def __init__(self, *, host: str = "127.0.0.1", port: int = 11111, **_: Any) -> None:
        self.host = host
        self.port = port
        self._connected = False

    def connect(self) -> None:
        try:
            import alpyca  # noqa: F401
        except ImportError as exc:
            raise _need("alpyca", "Alpaca Focuser") from exc
        raise DomainError("AlpacaFocuser: use backend=sim ate Omni Simulator", rule_id="AC-044")

    def disconnect(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def move(self, position: int) -> None:
        raise DomainError("focuser nao ligado", rule_id="RN-092")

    def get_position(self) -> int:
        return 0


class UdrvCameraStub:
    """Placeholder SBIG udrv — integracao no repo sbig-suite (AC-042)."""

    backend_name = "udrv"

    def connect(self, device: str = "usb") -> None:
        raise DomainError(
            "udrv SBIG vive no sbig-suite; adapter completo e AC-042 (repo separado). Use sim.",
            rule_id="AC-042",
        )

    def disconnect(self) -> None:
        return

    def is_connected(self) -> bool:
        return False

    def expose(self, *, exptime_s: float, frame_type: str = "light", binning: int = 1) -> dict:
        raise DomainError("udrv nao disponivel", rule_id="AC-042")

    def save_fits(self, path: Path, *, headers: dict[str, Any] | None = None) -> Path:
        raise DomainError("udrv nao disponivel", rule_id="AC-042")
