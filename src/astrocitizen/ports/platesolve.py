"""Porta de plate-solve / WCS (AC-110)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@dataclass
class PlateSolveResult:
    """Solucao WCS minima apos plate-solve."""

    ra_center_deg: float
    dec_center_deg: float
    scale_arcsec: float
    backend: str
    orientation_deg: float | None = None
    parity: int | None = None
    wcs_fits_path: Path | None = None
    meta: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class PlateSolvePort(Protocol):
    """Integra solver externo (astrometry.net local/remoto ou synthetic)."""

    def solve(
        self,
        fits_path: Path,
        *,
        out_dir: Path,
        ra_hint_deg: float | None = None,
        dec_hint_deg: float | None = None,
        radius_deg: float | None = None,
        scale_low_arcsec: float | None = None,
        scale_high_arcsec: float | None = None,
        timeout_s: float = 120.0,
    ) -> PlateSolveResult:
        """Resolve WCS; grava FITS com WCS em out_dir quando possivel."""
        ...
