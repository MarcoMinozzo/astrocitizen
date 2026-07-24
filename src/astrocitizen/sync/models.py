"""Modelos da fila de sincronização Desktop → SaaS (AC-222)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal
from uuid import UUID

SyncStatus = Literal["pending", "in_flight", "acked", "failed", "conflict"]
SyncOperation = Literal["create", "update", "upsert"]


@dataclass(slots=True)
class SyncQueueItem:
    id: UUID
    client_op_id: UUID
    workspace_id: UUID
    entity_type: str
    operation: SyncOperation
    payload: dict[str, Any] = field(default_factory=dict)
    status: SyncStatus = "pending"
    retry_count: int = 0
    last_error: str | None = None
    created_at: str = ""
    updated_at: str = ""
    acked_at: str | None = None
    server_id: str | None = None
