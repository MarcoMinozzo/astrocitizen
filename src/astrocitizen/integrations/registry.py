"""Registry de ObservatoryProvider (D-012 / E20)."""

from __future__ import annotations

from typing import Any, Iterable

from astrocitizen.integrations.aavso import AavsoProvider
from astrocitizen.integrations.bess import BessProvider
from astrocitizen.integrations.gaia import GaiaProvider
from astrocitizen.integrations.mpc import MpcProvider
from astrocitizen.integrations.sesame import SesameProvider
from astrocitizen.integrations.simbad import SimbadProvider
from astrocitizen.integrations.tns import TnsProvider
from astrocitizen.integrations.vizier import VizierProvider
from astrocitizen.integrations.vsx import VsxProvider
from astrocitizen.ports.observatory_provider import ObservatoryProvider
from astrocitizen.shared.errors import NotFoundError


def default_providers(*, archive: Any | None = None) -> list[ObservatoryProvider]:
    """Providers skeleton — wrappers sobre adapters/contribution existentes."""
    return [
        SesameProvider(archive=archive),
        SimbadProvider(archive=archive),
        VsxProvider(archive=archive),
        VizierProvider(archive=archive),
        GaiaProvider(archive=archive),
        AavsoProvider(archive=archive),
        MpcProvider(),
        TnsProvider(),
        BessProvider(),
    ]


class ProviderRegistry:
    """Descoberta por nome e por feature."""

    def __init__(self, providers: Iterable[ObservatoryProvider] | None = None) -> None:
        self._providers: dict[str, ObservatoryProvider] = {}
        for p in providers or default_providers():
            self.register(p)

    def register(self, provider: ObservatoryProvider) -> None:
        self._providers[provider.name] = provider

    def get(self, name: str) -> ObservatoryProvider:
        key = (name or "").strip().lower()
        if key not in self._providers:
            raise NotFoundError(f"provider desconhecido: {name}")
        return self._providers[key]

    def list_names(self) -> list[str]:
        return sorted(self._providers)

    def list_manifests(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for name in self.list_names():
            p = self._providers[name]
            rows.append(
                {
                    "name": p.name,
                    "features": sorted(p.features),
                }
            )
        return rows

    def with_feature(self, feature: str) -> list[ObservatoryProvider]:
        return [p for p in self._providers.values() if p.supports(feature)]
