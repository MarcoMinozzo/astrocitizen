"""Modelos de reducao / calibracao."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal
from uuid import UUID

MasterKind = Literal["bias", "dark", "flat"]


@dataclass(slots=True)
class CalibrationMaster:
    id: UUID
    workspace_id: UUID
    kind: MasterKind
    version_num: int
    artifact_id: UUID | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    notes: str = ""
    created_at: str = ""


@dataclass(slots=True)
class AnalysisProduct:
    id: UUID
    workspace_id: UUID
    product_type: str
    version_num: int = 1
    program_id: UUID | None = None
    parent_product_id: UUID | None = None
    is_publishable: bool = False
    parameters: dict[str, Any] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)
    state: str = "draft"
