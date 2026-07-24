"""Provider VSX — wrapper resolver AAVSO (D-012)."""

from __future__ import annotations

from typing import Any

from astrocitizen.adapters.sky.vsx_resolver import VsxResolver
from astrocitizen.integrations.base import BaseObservatoryProvider


class VsxProvider(BaseObservatoryProvider):
    name = "vsx"
    features = frozenset({"search"})

    def __init__(self, resolver: Any | None = None) -> None:
        self._resolver = resolver or VsxResolver()

    def search_object(self, name: str) -> dict[str, Any]:
        return self._resolver.resolve(name)
