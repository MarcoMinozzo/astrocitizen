"""Portas de efemerides e meteorologia."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class EphemerisPort(Protocol):
    """Calculo / consulta de efemerides observacionais (Astropy / Astroquery)."""

    def altitude_azimuth(
        self,
        *,
        ra_deg: float,
        dec_deg: float,
        latitude_deg: float,
        longitude_deg: float,
        elevation_m: float,
        utc_iso: str,
    ) -> dict[str, Any]:
        """Devolve alt/az/airmass (estrutura minima; expandir em E3)."""
        ...


@runtime_checkable
class MeteoPort(Protocol):
    """Condicoes / previsao meteo do Site (RN-020...024)."""

    def snapshot(self, *, latitude_deg: float, longitude_deg: float) -> dict[str, Any]:
        """Snapshot meteo associado ao local."""
        ...
