"""Modelos canónicos de observação (D-012) — independentes de formatos institucionais."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass(slots=True)
class Observation:
    """Observação / medida fotométrica ou genérica no domínio AstroCitizen."""

    object_name: str
    ra_deg: float | None = None
    dec_deg: float | None = None
    jd: float | None = None
    observer: str | None = None
    observatory_code: str | None = None
    instrument: str | None = None
    filter_name: str | None = None
    exposure_s: float | None = None
    snr: float | None = None
    mag: float | None = None
    mag_err: float | None = None
    id: UUID | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Spectrum:
    """Espectro 1D canónico (publicação via providers BeSS/ARAS/AAVSO/…)."""

    object_name: str
    wavelength: list[float] = field(default_factory=list)
    flux: list[float] = field(default_factory=list)
    uncertainty: list[float] = field(default_factory=list)
    resolution: float | None = None
    fits_header: dict[str, Any] = field(default_factory=dict)
    jd: float | None = None
    observer: str | None = None
    instrument: str | None = None
    id: UUID | None = None
    extra: dict[str, Any] = field(default_factory=dict)
