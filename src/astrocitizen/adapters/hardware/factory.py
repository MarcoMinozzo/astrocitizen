"""Factory de backends de hardware (AC-046)."""

from __future__ import annotations

from typing import Literal

from astrocitizen.adapters.hardware.simulators import (
    SimulatorCamera,
    SimulatorFocuser,
    SimulatorMount,
)
from astrocitizen.shared.errors import DomainError

BackendKind = Literal["sim", "alpaca", "udrv"]


def create_camera(backend: BackendKind = "sim", **kwargs):
    if backend == "sim":
        return SimulatorCamera(**kwargs)
    if backend == "alpaca":
        from astrocitizen.adapters.hardware.alpaca_stubs import AlpacaCamera

        return AlpacaCamera(**kwargs)
    if backend == "udrv":
        from astrocitizen.adapters.hardware.alpaca_stubs import UdrvCameraStub

        return UdrvCameraStub(**kwargs)
    raise DomainError(f"backend de camera desconhecido: {backend}")


def create_mount(backend: BackendKind = "sim", **kwargs):
    if backend == "sim":
        return SimulatorMount(**kwargs)
    if backend == "alpaca":
        from astrocitizen.adapters.hardware.alpaca_stubs import AlpacaMount

        return AlpacaMount(**kwargs)
    raise DomainError(f"backend de montagem desconhecido: {backend}")


def create_focuser(backend: BackendKind = "sim", **kwargs):
    if backend == "sim":
        return SimulatorFocuser(**kwargs)
    if backend == "alpaca":
        from astrocitizen.adapters.hardware.alpaca_stubs import AlpacaFocuser

        return AlpacaFocuser(**kwargs)
    raise DomainError(f"backend de focuser desconhecido: {backend}")
