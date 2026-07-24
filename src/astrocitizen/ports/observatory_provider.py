"""Port ObservatoryProvider — hub de interoperabilidade (D-012 / E20)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Protocol, runtime_checkable

from astrocitizen.domain.observation import Observation, Spectrum

ProviderFeature = Literal[
    "search",
    "lightcurve",
    "get_observations",
    "upload_photometry",
    "prepare_photometry",
    "upload_spectrum",
    "prepare_spectrum",
    "upload_astrometry",
    "prepare_astrometry",
    "prepare_transient",
    "authenticate",
]


@runtime_checkable
class ObservatoryProvider(Protocol):
    """Interface comum para catálogos e redes de publicação.

    Métodos concretos são opcionais: consultar `features` / `supports` antes.
    `prepare_*` gera artefacto oficial (AEF, FITS, ADES) sem upload HTTP.
    `upload_*` só quando a instituição documenta API de submissão.
    """

    @property
    def name(self) -> str:
        """Identificador estável (ex.: aavso, mpc, simbad)."""
        ...

    @property
    def features(self) -> frozenset[str]:
        """Capacidades declaradas (manifesto do guia)."""
        ...

    def supports(self, feature: str) -> bool:
        ...

    def authenticate(self, credentials: dict[str, Any] | None = None) -> None:
        """Opcional — valida/armazena credenciais da rede."""
        ...

    def search_object(self, name: str) -> dict[str, Any]:
        """Resolve / enriquece objecto (ra_deg, dec_deg, external_ids, …)."""
        ...

    def get_observations(self, object_name: str) -> list[dict[str, Any]]:
        """Consulta observações remotas (quando a API o permitir)."""
        ...

    def prepare_photometry(
        self, observation: Observation, *, out_path: Path, **kwargs: Any
    ) -> Path:
        """Gera ficheiro oficial de fotometria (ex.: AEF)."""
        ...

    def prepare_spectrum(
        self, spectrum: Spectrum, *, out_path: Path, **kwargs: Any
    ) -> Path:
        """Gera ficheiro oficial de espectro (ex.: BeSS FITS)."""
        ...

    def prepare_astrometry(
        self, observation: Observation, *, out_path: Path, **kwargs: Any
    ) -> Path:
        """Gera ficheiro oficial de astrometria (ex.: ADES PSV)."""
        ...

    def prepare_transient(
        self, observation: Observation, *, out_path: Path, **kwargs: Any
    ) -> Path:
        """Gera report de transiente (ex.: TNS JSON)."""
        ...
