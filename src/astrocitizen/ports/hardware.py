"""Portas de hardware do observatorio (Desktop)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class CameraPort(Protocol):
    """Camera: backends udrv | alpaca | sim (RN-032)."""

    backend_name: str

    def connect(self, device: str = "usb") -> None: ...

    def disconnect(self) -> None: ...

    def is_connected(self) -> bool: ...

    def expose(
        self,
        *,
        exptime_s: float,
        frame_type: str = "light",
        binning: int = 1,
    ) -> dict[str, Any]:
        """Dispara exposicao; devolve metadados (sem path)."""
        ...

    def save_fits(self, path: Path, *, headers: dict[str, Any] | None = None) -> Path:
        """Grava ultimo frame em FITS (imutavel apos escrita; RN-061)."""
        ...


@runtime_checkable
class MountPort(Protocol):
    """Montagem / telescopio (Alpaca Telescope)."""

    backend_name: str

    def connect(self) -> None: ...

    def disconnect(self) -> None: ...

    def is_connected(self) -> bool: ...

    def slew_radec(self, ra_deg: float, dec_deg: float) -> None: ...

    def get_radec(self) -> tuple[float, float]: ...


@runtime_checkable
class FocuserPort(Protocol):
    """Focuser (Alpaca Focuser)."""

    backend_name: str

    def connect(self) -> None: ...

    def disconnect(self) -> None: ...

    def is_connected(self) -> bool: ...

    def move(self, position: int) -> None: ...

    def get_position(self) -> int: ...
