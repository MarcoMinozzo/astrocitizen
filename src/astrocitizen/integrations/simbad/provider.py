"""Provider SIMBAD — wrapper resolver (D-012)."""

from __future__ import annotations

from typing import Any

from astrocitizen.adapters.sky.simbad_resolver import SimbadResolver
from astrocitizen.integrations.base import BaseObservatoryProvider


class SimbadProvider(BaseObservatoryProvider):
    name = "simbad"
    features = frozenset({"search"})

    def __init__(self, resolver: Any | None = None) -> None:
        self._resolver = resolver or SimbadResolver()

    def search_object(self, name: str) -> dict[str, Any]:
        return self._resolver.resolve(name)
