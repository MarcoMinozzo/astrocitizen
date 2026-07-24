"""Provider Gaia TAP — cone/source_id + cache local (AC-213 / D-013)."""

from __future__ import annotations

from typing import Any

from astrocitizen.adapters.sky.gaia_resolver import GaiaResolver
from astrocitizen.integrations.base import BaseObservatoryProvider
from astrocitizen.shared.timeutil import utc_now_iso


class GaiaProvider(BaseObservatoryProvider):
    name = "gaia"
    features = frozenset({"search"})

    def __init__(
        self,
        resolver: Any | None = None,
        *,
        archive: Any | None = None,
    ) -> None:
        self._resolver = resolver or GaiaResolver()
        self.archive = archive

    def search_object(self, name: str) -> dict[str, Any]:
        resolved = self._resolver.resolve(name)
        self._cache_write(name, resolved)
        return resolved

    def search_near(
        self, ra_deg: float, dec_deg: float, *, radius_arcsec: float = 5.0
    ) -> dict[str, Any]:
        resolved = self._resolver.resolve_near(
            ra_deg, dec_deg, radius_arcsec=radius_arcsec
        )
        key = f"{ra_deg:.5f},{dec_deg:.5f}"
        self._cache_write(key, resolved)
        return resolved

    def _cache_write(self, key: str, resolved: dict[str, Any]) -> None:
        if self.archive is None:
            return
        ids = dict(resolved.get("external_ids") or {})
        object_id = str(
            ids.get("gaia_source_id") or resolved.get("designation") or key
        ).strip()
        self.archive.upsert_institutional_cache(
            provider="gaia",
            object_id=object_id,
            payload=resolved,
            fetched_at=utc_now_iso(),
        )
        q = (key or "").strip()
        if q and q != object_id:
            self.archive.upsert_institutional_cache(
                provider="gaia",
                object_id=q,
                payload=resolved,
                fetched_at=utc_now_iso(),
            )
