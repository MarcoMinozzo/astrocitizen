"""Resolucao de conflitos multi-programa por prioridade (AC-037)."""

from __future__ import annotations

from datetime import datetime

from astrocitizen.planning.models import ObservationBlock


def _parse(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def windows_overlap(a: ObservationBlock, b: ObservationBlock) -> bool:
    a0, a1 = _parse(a.window_start_utc), _parse(a.window_end_utc)
    b0, b1 = _parse(b.window_start_utc), _parse(b.window_end_utc)
    return a0 < b1 and b0 < a1


def resolve_priority_conflicts(blocks: list[ObservationBlock]) -> list[ObservationBlock]:
    """Entre blocos 'agendado' sobrepostos, mantem o de menor priority; outros -> candidato."""
    scheduled = [b for b in blocks if b.status == "agendado"]
    scheduled.sort(key=lambda b: (b.priority, b.sort_order))
    winners: list[ObservationBlock] = []
    for block in scheduled:
        conflict = next((w for w in winners if windows_overlap(block, w)), None)
        if conflict is None:
            winners.append(block)
            continue
        block.status = "candidato"
        block.status_reason = (
            f"conflito com bloco prioridade {conflict.priority} "
            f"(id={conflict.id})"
        )
    return blocks
