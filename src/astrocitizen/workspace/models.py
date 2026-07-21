"""Workspace minimo (S1)."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class Workspace:
    id: UUID
    name: str
    version: int = 1
