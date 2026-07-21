"""Portas de hardware do observatorio (Desktop)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class CameraPort(Protocol):
    """Camera: backends udrv | alpaca | sim (RN-032)."""

    def connect(self, device: str = "usb") -> None: ...

    def disconnect(self) -> None: ...

    def is_connected(self) -> bool: ...


@runtime_checkable
class MountPort(Protocol):
    """Montagem / telescopio (Alpaca Telescope)."""

    def connect(self) -> None: ...

    def disconnect(self) -> None: ...

    def is_connected(self) -> bool: ...


@runtime_checkable
class FocuserPort(Protocol):
    """Focuser (Alpaca Focuser)."""

    def connect(self) -> None: ...

    def disconnect(self) -> None: ...

    def is_connected(self) -> bool: ...
