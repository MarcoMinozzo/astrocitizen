"""Modelos de contribuicao a redes cidadaes (AC-140)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass
class NetworkSubmission:
    id: UUID
    workspace_id: UUID
    network: str  # aavso | mpc | tns
    status: str  # draft | dry_run | submitted | failed
    artifact_uri: str | None = None
    product_id: UUID | None = None
    payload_summary: dict[str, Any] = field(default_factory=dict)
    remote_ack: str | None = None
    error: str | None = None
    created_at: str = ""
    updated_at: str = ""
    version: int = 1
