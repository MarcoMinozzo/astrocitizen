"""Identificadores e helpers de ID."""

from __future__ import annotations

import uuid
from typing import NewType

WorkspaceId = NewType("WorkspaceId", uuid.UUID)
SiteId = NewType("SiteId", uuid.UUID)
ProgramId = NewType("ProgramId", uuid.UUID)
ObservationId = NewType("ObservationId", uuid.UUID)


def new_id() -> uuid.UUID:
    """Gera UUID v4 para entidades de dominio."""
    return uuid.uuid4()
