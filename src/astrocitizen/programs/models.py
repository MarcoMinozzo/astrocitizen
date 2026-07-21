"""Entidades de programas observacionais."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal
from uuid import UUID

ProgramState = Literal["draft", "active", "paused", "archived"]


@dataclass(slots=True)
class ProgramTemplate:
    id: str
    class_: str
    name: str
    technique: str = ""
    default_networks: list[str] = field(default_factory=list)
    minimum_product: str = ""
    priority: str = "P3"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Program:
    id: UUID
    workspace_id: UUID
    template_id: str
    name: str
    state: ProgramState = "draft"
    priority: int = 10
    default_instrument_config_id: UUID | None = None
    export_networks: list[str] = field(default_factory=list)
    minimum_product: str = ""
    cadence: dict[str, Any] = field(default_factory=dict)
    settings: dict[str, Any] = field(default_factory=dict)
    version: int = 1
