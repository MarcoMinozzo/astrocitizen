"""Modelos de planejamento (S2)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal
from uuid import UUID

DailyPlanState = Literal["draft", "published", "in_execution", "closed"]

BlockStatus = Literal[
    "candidato",
    "agendado",
    "inviavel_ceu",
    "inviavel_meteo",
    "inviavel_equip",
    "em_execucao",
    "concluido",
    "pulado",
    "falhou",
]


@dataclass(slots=True)
class Target:
    id: UUID
    workspace_id: UUID
    designation: str
    ra_deg: float | None = None
    dec_deg: float | None = None
    target_type: str = "star"
    external_ids: dict[str, Any] = field(default_factory=dict)
    version: int = 1


@dataclass(slots=True)
class DailyPlan:
    id: UUID
    workspace_id: UUID
    site_id: UUID
    night_date: str  # YYYY-MM-DD
    state: DailyPlanState = "draft"
    generated_at: str = ""
    published_at: str | None = None
    version: int = 1


@dataclass(slots=True)
class ObservationBlock:
    id: UUID
    daily_plan_id: UUID
    window_start_utc: str
    window_end_utc: str
    program_id: UUID | None = None
    target_id: UUID | None = None
    instrument_config_id: UUID | None = None
    sort_order: int = 0
    predicted_altitude_deg: float | None = None
    airmass: float | None = None
    status: BlockStatus = "candidato"
    status_reason: str | None = None
    priority: int = 10
    notes: str = ""
    ephemeris_snapshot_id: UUID | None = None
    meteo_snapshot_id: UUID | None = None
    technique: str | None = None
    version: int = 1


@dataclass(slots=True)
class MeteoSnapshot:
    id: UUID
    workspace_id: UUID
    site_id: UUID
    captured_at_utc: str
    source: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class EphemerisSnapshot:
    id: UUID
    workspace_id: UUID
    site_id: UUID
    epoch_utc: str
    source: str
    target_id: UUID | None = None
    payload: dict[str, Any] = field(default_factory=dict)
