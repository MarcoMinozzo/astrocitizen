"""Porta de arquivo / persistencia de dominio (BD mestre ou espelho)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID

from astrocitizen.inventory.models import Equipment, InstrumentConfig, Site
from astrocitizen.observatory.models import ObservationRecord, Session
from astrocitizen.planning.models import (
    DailyPlan,
    EphemerisSnapshot,
    MeteoSnapshot,
    ObservationBlock,
    Target,
)
from astrocitizen.programs.models import Program, ProgramTemplate
from astrocitizen.workspace.models import Workspace


@runtime_checkable
class ArchivePort(Protocol):
    """Persistencia de entidades de dominio (RN-110...116).

    Implementacoes: SQLite (Desktop), PostgreSQL (SaaS). Detalhe: MODELO_DADOS_V1.
    """

    def healthcheck(self) -> bool:
        """Retorna True se a ligacao ao arquivo estiver operacional."""
        ...

    def migrate(self) -> int:
        """Aplica migracoes pendentes; devolve versao actual do schema."""
        ...

    # --- workspace ---
    def upsert_workspace(self, workspace: Workspace) -> Workspace: ...

    def get_workspace(self, workspace_id: UUID) -> Workspace | None: ...

    def list_workspaces(self) -> list[Workspace]: ...

    # --- sites ---
    def upsert_site(self, site: Site) -> Site: ...

    def get_site(self, site_id: UUID) -> Site | None: ...

    def list_sites(self, workspace_id: UUID) -> list[Site]: ...

    def soft_delete_site(self, site_id: UUID) -> None: ...

    # --- equipment ---
    def upsert_equipment(self, equipment: Equipment) -> Equipment: ...

    def get_equipment(self, equipment_id: UUID) -> Equipment | None: ...

    def list_equipment(self, workspace_id: UUID) -> list[Equipment]: ...

    def soft_delete_equipment(self, equipment_id: UUID) -> None: ...

    # --- instrument configs ---
    def upsert_instrument_config(self, config: InstrumentConfig) -> InstrumentConfig: ...

    def get_instrument_config(self, config_id: UUID) -> InstrumentConfig | None: ...

    def list_instrument_configs(self, workspace_id: UUID) -> list[InstrumentConfig]: ...

    # --- program templates ---
    def upsert_program_template(self, template: ProgramTemplate) -> ProgramTemplate: ...

    def get_program_template(self, template_id: str) -> ProgramTemplate | None: ...

    def list_program_templates(self, *, class_: str | None = None) -> list[ProgramTemplate]: ...

    # --- programs ---
    def upsert_program(self, program: Program) -> Program: ...

    def get_program(self, program_id: UUID) -> Program | None: ...

    def list_programs(self, workspace_id: UUID, *, state: str | None = None) -> list[Program]: ...

    def soft_delete_program(self, program_id: UUID) -> None: ...

    # --- targets (S2) ---
    def upsert_target(self, target: Target) -> Target: ...

    def get_target(self, target_id: UUID) -> Target | None: ...

    def list_targets(self, workspace_id: UUID) -> list[Target]: ...

    def link_program_target(
        self,
        program_id: UUID,
        target_id: UUID,
        *,
        role: str = "primary",
        sort_order: int = 0,
    ) -> None: ...

    def list_program_targets(self, program_id: UUID) -> list[tuple[Target, str, int]]: ...

    # --- daily plans (S2) ---
    def upsert_daily_plan(self, plan: DailyPlan) -> DailyPlan: ...

    def get_daily_plan(self, plan_id: UUID) -> DailyPlan | None: ...

    def get_daily_plan_for_night(
        self,
        workspace_id: UUID,
        site_id: UUID,
        night_date: str,
    ) -> DailyPlan | None: ...

    def list_daily_plans(
        self, workspace_id: UUID, *, site_id: UUID | None = None
    ) -> list[DailyPlan]: ...

    def replace_observation_blocks(
        self,
        daily_plan_id: UUID,
        blocks: list[ObservationBlock],
    ) -> list[ObservationBlock]: ...

    def list_observation_blocks(self, daily_plan_id: UUID) -> list[ObservationBlock]: ...

    def update_observation_block(self, block: ObservationBlock) -> ObservationBlock: ...

    def get_observation_block(self, block_id: UUID) -> ObservationBlock | None: ...

    # --- snapshots (S2) ---
    def save_meteo_snapshot(self, snap: MeteoSnapshot) -> MeteoSnapshot: ...

    def save_ephemeris_snapshot(self, snap: EphemerisSnapshot) -> EphemerisSnapshot: ...

    # --- sessions (S3) ---
    def upsert_session(self, session: Session) -> Session: ...

    def get_session(self, session_id: UUID) -> Session | None: ...

    def list_sessions(self, workspace_id: UUID, *, state: str | None = None) -> list[Session]: ...

    def add_session_event(
        self,
        *,
        event_id: UUID,
        session_id: UUID,
        event_type: str,
        occurred_at_utc: str,
        block_id: UUID | None = None,
        payload: dict | None = None,
    ) -> None: ...

    def save_observation(self, obs: ObservationRecord) -> ObservationRecord: ...

    def save_artifact(
        self,
        *,
        artifact_id: UUID,
        workspace_id: UUID,
        kind: str,
        uri: str,
        filename: str,
        observation_id: UUID | None = None,
        size_bytes: int | None = None,
    ) -> UUID: ...

    # --- observations ---
    def create_observation(
        self,
        *,
        observation_id: UUID,
        workspace_id: UUID,
        observed_at_utc: str,
        site_id: UUID | None = None,
        program_id: UUID | None = None,
        simulated: bool = False,
        notes: str = "",
    ) -> UUID: ...

    def list_observations(
        self,
        workspace_id: UUID,
        *,
        include_simulated: bool = False,
    ) -> list[dict]: ...

    def soft_delete_observation(self, observation_id: UUID) -> None: ...

    # --- audit ---
    def list_audit(
        self,
        workspace_id: UUID | None = None,
        *,
        limit: int = 100,
    ) -> list[dict]: ...
