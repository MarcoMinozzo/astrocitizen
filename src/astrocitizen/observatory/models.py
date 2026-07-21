"""Modelos de sessao observacional (S3)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal
from uuid import UUID

SessionState = Literal["active", "ended", "aborted"]


@dataclass(slots=True)
class Session:
    id: UUID
    workspace_id: UUID
    site_id: UUID
    daily_plan_id: UUID
    daily_plan_version: int
    started_at_utc: str
    state: SessionState = "active"
    plan_snapshot: dict[str, Any] = field(default_factory=dict)
    ended_at_utc: str | None = None
    meteo_start_id: UUID | None = None
    meteo_end_id: UUID | None = None
    device_id: UUID | None = None
    client_id: UUID | None = None
    version: int = 1


@dataclass(slots=True)
class ObservationRecord:
    id: UUID
    workspace_id: UUID
    observed_at_utc: str
    site_id: UUID | None = None
    session_id: UUID | None = None
    block_id: UUID | None = None
    program_id: UUID | None = None
    target_id: UUID | None = None
    instrument_config_id: UUID | None = None
    state: str = "raw"
    camera_backend: str | None = None
    simulated: bool = False
    meteo_manual: bool = False
    meteo_snapshot_id: UUID | None = None
    headers_summary: dict[str, Any] = field(default_factory=dict)
    notes: str = ""
    version: int = 1
