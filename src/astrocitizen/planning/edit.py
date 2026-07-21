"""Edicao manual de blocos do ProgramaDiario (AC-035 / RN-052)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from astrocitizen.planning.models import ObservationBlock
from astrocitizen.shared.errors import DomainError, NotFoundError


class EditDailyPlan:
    def __init__(self, archive: Any) -> None:
        self.archive = archive

    def set_block_status(
        self,
        block_id: UUID,
        status: str,
        *,
        reason: str | None = None,
        notes: str | None = None,
    ) -> ObservationBlock:
        block = self.archive.get_observation_block(block_id)
        if block is None:
            raise NotFoundError(f"bloco nao encontrado: {block_id}")
        plan = self.archive.get_daily_plan(block.daily_plan_id)
        if plan is None:
            raise NotFoundError(f"plano nao encontrado: {block.daily_plan_id}")
        if plan.state not in ("draft", "published"):
            raise DomainError(
                f"plano em estado '{plan.state}' nao editavel",
                rule_id="RN-052",
            )
        block.status = status  # type: ignore[assignment]
        if reason is not None:
            block.status_reason = reason
        if notes is not None:
            block.notes = notes
        return self.archive.update_observation_block(block)

    def reorder(self, daily_plan_id: UUID, block_ids: list[UUID]) -> list[ObservationBlock]:
        plan = self.archive.get_daily_plan(daily_plan_id)
        if plan is None:
            raise NotFoundError(f"plano nao encontrado: {daily_plan_id}")
        if plan.state not in ("draft", "published"):
            raise DomainError("plano nao editavel", rule_id="RN-052")
        blocks = {b.id: b for b in self.archive.list_observation_blocks(daily_plan_id)}
        if set(block_ids) != set(blocks):
            raise DomainError("lista de blocos incompleta ou invalida", rule_id="RN-052")
        updated: list[ObservationBlock] = []
        for i, bid in enumerate(block_ids):
            b = blocks[bid]
            b.sort_order = i
            updated.append(self.archive.update_observation_block(b))
        return updated
