"""Provider VSX — wrapper resolver AAVSO + cache local (D-012 / D-013)."""

from __future__ import annotations

from typing import Any

from astrocitizen.adapters.sky.vsx_resolver import VsxResolver
from astrocitizen.integrations.base import BaseObservatoryProvider
from astrocitizen.shared.timeutil import utc_now_iso


class VsxProvider(BaseObservatoryProvider):
    name = "vsx"
    features = frozenset({"search"})

    def __init__(
        self,
        resolver: Any | None = None,
        *,
        archive: Any | None = None,
    ) -> None:
        self._resolver = resolver or VsxResolver()
        self.archive = archive

    def search_object(self, name: str) -> dict[str, Any]:
        resolved = self._resolver.resolve(name)
        if self.archive is not None:
            ids = dict(resolved.get("external_ids") or {})
            object_id = str(
                ids.get("auid")
                or ids.get("vsx")
                or resolved.get("designation")
                or name
            ).strip()
            self.archive.upsert_institutional_cache(
                provider="vsx",
                object_id=object_id,
                payload=resolved,
                fetched_at=utc_now_iso(),
            )
            # Tambem indexar pelo nome pedido
            q = (name or "").strip()
            if q and q != object_id:
                self.archive.upsert_institutional_cache(
                    provider="vsx",
                    object_id=q,
                    payload=resolved,
                    fetched_at=utc_now_iso(),
                )
        return resolved
