"""Entidades de inventario: Site e Equipamento."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass(slots=True)
class Site:
    id: UUID
    workspace_id: UUID
    name: str
    latitude_deg: float
    longitude_deg: float
    elevation_m: float = 0.0
    timezone: str = "UTC"
    min_altitude_deg: float = 25.0
    night_start_rule: str = "astronomical_twilight"
    meteo_thresholds: dict[str, Any] = field(default_factory=dict)
    is_default: bool = False
    version: int = 1


@dataclass(slots=True)
class Equipment:
    id: UUID
    workspace_id: UUID
    type: str
    name: str
    backend: str | None = None
    available: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    version: int = 1


@dataclass(slots=True)
class InstrumentConfig:
    id: UUID
    workspace_id: UUID
    name: str
    notes: str = ""
    items: dict[str, UUID] = field(default_factory=dict)  # role -> equipment_id
    version: int = 1
