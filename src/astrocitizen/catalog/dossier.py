"""CatalogDossierService — busca multi-API → ficha → nosso catálogo (AC-235)."""

from __future__ import annotations

from typing import Any, Sequence
from uuid import UUID

from astrocitizen.catalog.models import CatalogObject, dossier_from_resolved
from astrocitizen.integrations.catalog_service import (
    DEFAULT_PROVIDERS,
    CatalogResolveService,
)
from astrocitizen.shared.ids import new_id
from astrocitizen.shared.timeutil import utc_now_iso


class CatalogDossierService:
    """Resolve em todas as APIs, monta ficha por secções e faz upsert no store."""

    def __init__(
        self,
        archive: Any,
        resolve_service: CatalogResolveService | None = None,
    ) -> None:
        self.archive = archive
        self.resolve = resolve_service or CatalogResolveService(archive)

    def persist_resolved(
        self,
        workspace_id: UUID,
        query: str,
        resolved: dict[str, Any],
        *,
        enqueue_sync: bool = True,
    ) -> CatalogObject:
        """Grava/actualiza ficha a partir de um payload já resolvido."""
        q = (query or "").strip()
        if not q:
            from astrocitizen.shared.errors import NotFoundError

            raise NotFoundError("nome vazio")

        now = utc_now_iso()
        sections = dossier_from_resolved(resolved, query=q, fetched_at=now)
        sources = list(resolved.get("sources") or [])
        designation = str(
            sections["identity"].get("designation")
            or resolved.get("designation")
            or q
        )

        existing = self.archive.find_catalog_object(workspace_id, q)
        if existing is None:
            existing = self.archive.find_catalog_object_by_designation(
                workspace_id, designation
            )

        obj = CatalogObject(
            id=existing.id if existing else new_id(),
            workspace_id=workspace_id,
            query_name=q,
            designation=designation,
            ra_deg=(
                float(resolved["ra_deg"]) if resolved.get("ra_deg") is not None else None
            ),
            dec_deg=(
                float(resolved["dec_deg"])
                if resolved.get("dec_deg") is not None
                else None
            ),
            sections=sections,
            sources=sources,
            fetched_at=now,
            updated_at=now,
            version=(existing.version + 1) if existing else 1,
        )
        saved = self.archive.upsert_catalog_object(obj)

        if enqueue_sync:
            try:
                from astrocitizen.sync.service import SyncEnqueueService

                SyncEnqueueService(self.archive).enqueue_catalog_object(saved.id)
            except Exception:
                # Sync opcional — ficha local prevalece
                pass
        return saved

    def lookup(
        self,
        workspace_id: UUID,
        name: str,
        *,
        network: bool = True,
        providers: Sequence[str] = DEFAULT_PROVIDERS,
        enqueue_sync: bool = True,
    ) -> CatalogObject:
        query = (name or "").strip()
        if not query:
            from astrocitizen.shared.errors import NotFoundError

            raise NotFoundError("nome vazio")

        if network:
            resolved = self.resolve.resolve(
                query, providers=providers, use_cache=True, network=True
            )
        else:
            resolved = self.resolve.resolve_from_cache(query, providers=providers)
            if resolved is None or resolved.get("ra_deg") is None:
                from astrocitizen.shared.errors import NotFoundError

                raise NotFoundError(f"sem ficha em cache: {query}")

        return self.persist_resolved(
            workspace_id, query, resolved, enqueue_sync=enqueue_sync
        )

    def get(self, object_id: UUID) -> CatalogObject | None:
        return self.archive.get_catalog_object(object_id)

    def list(self, workspace_id: UUID, *, limit: int = 100) -> list[CatalogObject]:
        return self.archive.list_catalog_objects(workspace_id, limit=limit)
