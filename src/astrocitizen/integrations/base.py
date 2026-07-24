"""Base para providers de integração (D-012)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from astrocitizen.domain.observation import Observation, Spectrum
from astrocitizen.shared.errors import DomainError


class BaseObservatoryProvider:
    """Implementação parcial: `supports` + erros claros se feature ausente."""

    name: str = "base"
    features: frozenset[str] = frozenset()

    def supports(self, feature: str) -> bool:
        return feature in self.features

    def authenticate(self, credentials: dict[str, Any] | None = None) -> None:
        self._require("authenticate")

    def search_object(self, name: str) -> dict[str, Any]:
        self._require("search")
        raise DomainError(f"{self.name}: search_object nao implementado", rule_id="D-012")

    def get_observations(self, object_name: str) -> list[dict[str, Any]]:
        self._require("get_observations")
        raise DomainError(
            f"{self.name}: get_observations nao implementado", rule_id="D-012"
        )

    def prepare_photometry(
        self, observation: Observation, *, out_path: Path, **kwargs: Any
    ) -> Path:
        self._require("prepare_photometry")
        raise DomainError(
            f"{self.name}: prepare_photometry nao implementado", rule_id="D-012"
        )

    def prepare_spectrum(
        self, spectrum: Spectrum, *, out_path: Path, **kwargs: Any
    ) -> Path:
        self._require("prepare_spectrum")
        raise DomainError(
            f"{self.name}: prepare_spectrum nao implementado", rule_id="D-012"
        )

    def prepare_astrometry(
        self, observation: Observation, *, out_path: Path, **kwargs: Any
    ) -> Path:
        self._require("prepare_astrometry")
        raise DomainError(
            f"{self.name}: prepare_astrometry nao implementado", rule_id="D-012"
        )

    def prepare_transient(
        self, observation: Observation, *, out_path: Path, **kwargs: Any
    ) -> Path:
        self._require("prepare_transient")
        raise DomainError(
            f"{self.name}: prepare_transient nao implementado", rule_id="D-012"
        )

    def _require(self, feature: str) -> None:
        if not self.supports(feature):
            raise DomainError(
                f"{self.name} nao declara feature '{feature}'",
                rule_id="D-012",
            )
