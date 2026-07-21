"""Portas de efemerides, meteorologia, radar e resolucao de alvos."""

from __future__ import annotations

from pathlib import Path
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
        """Devolve alt_deg, az_deg, airmass."""
        ...

    def night_window(
        self,
        *,
        latitude_deg: float,
        longitude_deg: float,
        elevation_m: float,
        night_date: str,
        night_start_rule: str = "astronomical_twilight",
    ) -> dict[str, str]:
        """Devolve start_utc / end_utc da noite civil (ISO-Z)."""
        ...


@runtime_checkable
class MeteoPort(Protocol):
    """Condicoes / previsao meteo do Site (RN-020...024)."""

    def snapshot(self, *, latitude_deg: float, longitude_deg: float) -> dict[str, Any]:
        """Snapshot actual no Site."""
        ...

    def forecast(
        self,
        *,
        latitude_deg: float,
        longitude_deg: float,
        start_utc: str | None = None,
        end_utc: str | None = None,
    ) -> dict[str, Any]:
        """Previsao horaria (opcionalmente limitada a [start,end]).

        Devolve dict com current-like fields (resumo) + chave `hourly` (lista).
        """
        ...


@runtime_checkable
class RadarPort(Protocol):
    """Imagem de radar de precipitacao na regiao do Site."""

    def region_image(
        self,
        *,
        latitude_deg: float,
        longitude_deg: float,
        zoom: int = 6,
        size: int = 512,
        out_path: Path | None = None,
    ) -> dict[str, Any]:
        """Descarrega PNG centrado no Site; devolve metadados + path/uri."""
        ...


@runtime_checkable
class TargetResolverPort(Protocol):
    """Resolve designacao -> coordenadas (SIMBAD / catalogo)."""

    def resolve(self, name: str) -> dict[str, Any]:
        """Devolve ra_deg, dec_deg, external_ids."""
        ...
