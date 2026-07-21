"""Politica de falha de instrumento (RN-092)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from astrocitizen.shared.errors import DomainError, NotFoundError
from astrocitizen.shared.ids import new_id
from astrocitizen.shared.timeutil import utc_now_iso


def mark_block_failed(
    archive: Any,
    *,
    session_id: UUID,
    block_id: UUID,
    reason: str,
    auto_advance: bool = False,
) -> None:
    """Marca bloco como falhou; default nao avanca automaticamente (RN-092)."""
    block = archive.get_observation_block(block_id)
    if block is None:
        raise NotFoundError(f"bloco nao encontrado: {block_id}")
    block.status = "falhou"
    block.status_reason = reason
    archive.update_observation_block(block)
    archive.add_session_event(
        event_id=new_id(),
        session_id=session_id,
        event_type="block.failed",
        occurred_at_utc=utc_now_iso(),
        block_id=block_id,
        payload={"reason": reason, "auto_advance": auto_advance},
    )
    if auto_advance:
        raise DomainError(
            "auto_advance ainda nao implementado; politica default e pausar",
            rule_id="RN-092",
        )
