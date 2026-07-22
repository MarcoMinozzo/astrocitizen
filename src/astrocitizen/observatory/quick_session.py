"""Preparacao de sessao para wizard GUI (IN-CAP)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from astrocitizen.observatory.session import ExecuteSession
from astrocitizen.planning.models import DailyPlan, ObservationBlock
from astrocitizen.shared.errors import DomainError, NotFoundError
from astrocitizen.shared.ids import new_id
from astrocitizen.shared.timeutil import utc_now_iso


@dataclass(slots=True)
class WizardSessionContext:
    session: Any
    plan: DailyPlan
    block: ObservationBlock
    created_session: bool


def _night_date(value: str | None) -> str:
    if value:
        return value
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _window_pair() -> tuple[str, str]:
    start = datetime.now(timezone.utc).replace(microsecond=0)
    end = start + timedelta(hours=4)

    def fmt(d: datetime) -> str:
        return d.isoformat().replace("+00:00", "Z")

    return fmt(start), fmt(end)


def prepare_wizard_session(
    archive: Any,
    *,
    workspace_id: UUID,
    site_id: UUID,
    program_id: UUID,
    target_id: UUID,
    night_date: str | None = None,
) -> WizardSessionContext:
    """Garante plano + bloco agendado e sessao activa (reusa se ja existir)."""
    site = archive.get_site(site_id)
    if site is None or site.workspace_id != workspace_id:
        raise NotFoundError("site invalido")
    program = archive.get_program(program_id)
    if program is None or program.workspace_id != workspace_id:
        raise NotFoundError("programa invalido")
    target = archive.get_target(target_id)
    if target is None or target.workspace_id != workspace_id:
        raise NotFoundError("alvo invalido")

    night = _night_date(night_date)
    plan = archive.get_daily_plan_for_night(workspace_id, site_id, night)
    if plan is None:
        plan = archive.upsert_daily_plan(
            DailyPlan(
                id=new_id(),
                workspace_id=workspace_id,
                site_id=site_id,
                night_date=night,
                state="draft",
                generated_at=utc_now_iso(),
            )
        )
    elif plan.state == "closed":
        plan.state = "draft"
        plan = archive.upsert_daily_plan(plan)

    # reuse active session for this plan
    active = [
        s
        for s in archive.list_sessions(workspace_id, state="active")
        if s.daily_plan_id == plan.id
    ]
    created = False
    if active:
        session = active[0]
    else:
        # other active sessions on different plans are ok
        session = ExecuteSession(archive).start(
            workspace_id=workspace_id, plan_id=plan.id
        )
        created = True

    existing = archive.list_observation_blocks(plan.id)
    block = next(
        (
            b
            for b in existing
            if b.program_id == program_id
            and b.target_id == target_id
            and b.status in ("candidato", "agendado", "em_execucao", "concluido")
        ),
        None,
    )
    if block is None:
        w0, w1 = _window_pair()
        block = archive.add_observation_block(
            ObservationBlock(
                id=new_id(),
                daily_plan_id=plan.id,
                program_id=program_id,
                target_id=target_id,
                instrument_config_id=program.default_instrument_config_id,
                sort_order=len(existing),
                window_start_utc=w0,
                window_end_utc=w1,
                status="agendado",
                priority=program.priority,
                technique=None,
                notes="wizard IN-CAP",
            )
        )
    else:
        block.status = "agendado"
        block.status_reason = None
        block = archive.update_observation_block(block)

    return WizardSessionContext(
        session=session,
        plan=plan,
        block=block,
        created_session=created,
    )


def reset_block_for_capture(archive: Any, block_id: UUID) -> ObservationBlock:
    block = archive.get_observation_block(block_id)
    if block is None:
        raise NotFoundError("bloco nao encontrado")
    if block.status == "falhou":
        raise DomainError("bloco falhou; escolha outro alvo/programa", rule_id="RN-092")
    block.status = "agendado"
    block.status_reason = None
    return archive.update_observation_block(block)
