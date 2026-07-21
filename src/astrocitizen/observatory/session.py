"""Caso de uso ExecutarSessao — congela ProgramaDiario (RN-056)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from astrocitizen.observatory.models import Session
from astrocitizen.shared.errors import DomainError, NotFoundError
from astrocitizen.shared.ids import new_id
from astrocitizen.shared.timeutil import utc_now_iso


def build_plan_snapshot(archive: Any, plan_id: UUID) -> dict[str, Any]:
    plan = archive.get_daily_plan(plan_id)
    if plan is None:
        raise NotFoundError(f"plano nao encontrado: {plan_id}")
    blocks = archive.list_observation_blocks(plan_id)
    return {
        "schema": 1,
        "plan": {
            "id": str(plan.id),
            "workspace_id": str(plan.workspace_id),
            "site_id": str(plan.site_id),
            "night_date": plan.night_date,
            "state": plan.state,
            "version": plan.version,
            "generated_at": plan.generated_at,
        },
        "blocks": [
            {
                "id": str(b.id),
                "program_id": str(b.program_id) if b.program_id else None,
                "target_id": str(b.target_id) if b.target_id else None,
                "sort_order": b.sort_order,
                "status": b.status,
                "status_reason": b.status_reason,
                "priority": b.priority,
                "window_start_utc": b.window_start_utc,
                "window_end_utc": b.window_end_utc,
                "predicted_altitude_deg": b.predicted_altitude_deg,
                "technique": b.technique,
            }
            for b in blocks
        ],
    }


class ExecuteSession:
    """Inicia sessao com snapshot imutavel do plano diario."""

    def __init__(self, archive: Any) -> None:
        self.archive = archive

    def start(
        self,
        *,
        workspace_id: UUID,
        plan_id: UUID,
        meteo_start_id: UUID | None = None,
    ) -> Session:
        plan = self.archive.get_daily_plan(plan_id)
        if plan is None or plan.workspace_id != workspace_id:
            raise NotFoundError(f"plano nao encontrado: {plan_id}")
        if plan.state in ("closed",):
            raise DomainError(f"plano '{plan.state}' nao inicia sessao", rule_id="RN-056")

        active = self.archive.list_sessions(workspace_id, state="active")
        if any(s.daily_plan_id == plan_id for s in active):
            raise DomainError("ja existe sessao activa para este plano", rule_id="RN-056")

        snapshot = build_plan_snapshot(self.archive, plan_id)
        session = Session(
            id=new_id(),
            workspace_id=workspace_id,
            site_id=plan.site_id,
            daily_plan_id=plan.id,
            daily_plan_version=plan.version,
            started_at_utc=utc_now_iso(),
            state="active",
            plan_snapshot=snapshot,
            meteo_start_id=meteo_start_id,
        )
        session = self.archive.upsert_session(session)

        plan.state = "in_execution"
        self.archive.upsert_daily_plan(plan)

        self.archive.add_session_event(
            event_id=new_id(),
            session_id=session.id,
            event_type="session.started",
            occurred_at_utc=session.started_at_utc,
            payload={"daily_plan_version": plan.version},
        )
        return session

    def end(self, session_id: UUID, *, abort: bool = False) -> Session:
        session = self.archive.get_session(session_id)
        if session is None:
            raise NotFoundError(f"sessao nao encontrada: {session_id}")
        if session.state != "active":
            raise DomainError(f"sessao ja em estado '{session.state}'")

        session.state = "aborted" if abort else "ended"
        session.ended_at_utc = utc_now_iso()
        session = self.archive.upsert_session(session)

        plan = self.archive.get_daily_plan(session.daily_plan_id)
        if plan is not None:
            plan.state = "closed"
            self.archive.upsert_daily_plan(plan)

        self.archive.add_session_event(
            event_id=new_id(),
            session_id=session.id,
            event_type="session.aborted" if abort else "session.ended",
            occurred_at_utc=session.ended_at_utc,
        )
        return session
