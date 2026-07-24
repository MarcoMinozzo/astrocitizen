"""Serviço de enfileiramento local (AC-222)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from astrocitizen.shared.ids import new_id
from astrocitizen.shared.timeutil import utc_now_iso
from astrocitizen.sync.canonical import (
    network_submission_canonical,
    observation_canonical,
)
from astrocitizen.sync.models import SyncQueueItem


class SyncEnqueueService:
    """Enfileira entidades canónicas na sync_queue do Archive."""

    def __init__(self, archive: Any) -> None:
        self.archive = archive

    def enqueue_observation(
        self, observation_id: UUID, *, operation: str = "upsert"
    ) -> SyncQueueItem:
        obs = self.archive.get_observation(observation_id)
        if obs is None:
            from astrocitizen.shared.errors import NotFoundError

            raise NotFoundError(f"observation nao encontrada: {observation_id}")
        return self.archive.enqueue_sync(
            SyncQueueItem(
                id=new_id(),
                client_op_id=new_id(),
                workspace_id=obs.workspace_id,
                entity_type="observation",
                operation=operation,  # type: ignore[arg-type]
                payload=observation_canonical(obs),
                status="pending",
                created_at=utc_now_iso(),
                updated_at=utc_now_iso(),
            )
        )

    def enqueue_network_submission(
        self, submission_id: UUID, *, operation: str = "upsert"
    ) -> SyncQueueItem:
        sub = self.archive.get_network_submission(submission_id)
        if sub is None:
            from astrocitizen.shared.errors import NotFoundError

            raise NotFoundError(f"submission nao encontrada: {submission_id}")
        return self.archive.enqueue_sync(
            SyncQueueItem(
                id=new_id(),
                client_op_id=new_id(),
                workspace_id=sub.workspace_id,
                entity_type="network_submission",
                operation=operation,  # type: ignore[arg-type]
                payload=network_submission_canonical(sub),
                status="pending",
                created_at=utc_now_iso(),
                updated_at=utc_now_iso(),
            )
        )
