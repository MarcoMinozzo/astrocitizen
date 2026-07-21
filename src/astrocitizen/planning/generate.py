"""Caso de uso: gerar / regenerar ProgramaDiario (RN-050...054)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from astrocitizen.planning.conflicts import resolve_priority_conflicts
from astrocitizen.planning.equipment_rules import validate_instrument_config
from astrocitizen.planning.meteo_rules import evaluate_meteo_window
from astrocitizen.planning.models import (
    DailyPlan,
    EphemerisSnapshot,
    MeteoSnapshot,
    ObservationBlock,
)
from astrocitizen.shared.errors import DomainError, NotFoundError
from astrocitizen.shared.ids import new_id
from astrocitizen.shared.timeutil import utc_now_iso


def _midpoint_iso(start_utc: str, end_utc: str) -> str:
    a = datetime.fromisoformat(start_utc.replace("Z", "+00:00"))
    b = datetime.fromisoformat(end_utc.replace("Z", "+00:00"))
    mid = a + (b - a) / 2
    return mid.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _shift_window(start: str, end: str, hours: float) -> tuple[str, str]:
    a = datetime.fromisoformat(start.replace("Z", "+00:00")) + timedelta(hours=hours)
    b = datetime.fromisoformat(end.replace("Z", "+00:00")) + timedelta(hours=hours)
    fmt = lambda d: d.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return fmt(a), fmt(b)


class GenerateDailyPlan:
    """Gera ProgramaDiario a partir de programas ativos + ceu + meteo + equipamento."""

    def __init__(
        self,
        archive: Any,
        ephemeris: Any,
        meteo: Any,
    ) -> None:
        self.archive = archive
        self.ephemeris = ephemeris
        self.meteo = meteo

    def execute(
        self,
        *,
        workspace_id: UUID,
        site_id: UUID,
        night_date: str,
    ) -> DailyPlan:
        site = self.archive.get_site(site_id)
        if site is None or site.workspace_id != workspace_id:
            raise NotFoundError(f"site nao encontrado: {site_id}")

        programs = self.archive.list_programs(workspace_id, state="active")
        equipment = {e.id: e for e in self.archive.list_equipment(workspace_id)}

        night = self.ephemeris.night_window(
            latitude_deg=site.latitude_deg,
            longitude_deg=site.longitude_deg,
            elevation_m=site.elevation_m,
            night_date=night_date,
            night_start_rule=site.night_start_rule,
        )
        start_utc, end_utc = night["start_utc"], night["end_utc"]
        mid_utc = _midpoint_iso(start_utc, end_utc)

        meteo_payload = self.meteo.forecast(
            latitude_deg=site.latitude_deg,
            longitude_deg=site.longitude_deg,
            start_utc=start_utc,
            end_utc=end_utc,
        )
        meteo_ok, meteo_reason = evaluate_meteo_window(meteo_payload, site.meteo_thresholds)
        meteo_snap = self.archive.save_meteo_snapshot(
            MeteoSnapshot(
                id=new_id(),
                workspace_id=workspace_id,
                site_id=site_id,
                captured_at_utc=utc_now_iso(),
                source=str(meteo_payload.get("source", "api")),
                payload=meteo_payload,
            )
        )

        existing = self.archive.get_daily_plan_for_night(workspace_id, site_id, night_date)
        if existing is not None and existing.state not in ("draft",):
            raise DomainError(
                f"plano {existing.id} em estado '{existing.state}' nao regeneravel",
                rule_id="RN-050",
            )

        plan = existing or DailyPlan(
            id=new_id(),
            workspace_id=workspace_id,
            site_id=site_id,
            night_date=night_date,
            state="draft",
        )
        plan.generated_at = utc_now_iso()
        plan.state = "draft"
        plan = self.archive.upsert_daily_plan(plan)

        blocks: list[ObservationBlock] = []
        sort_order = 0
        # Stagger windows slightly by program order to allow conflict demos when same night
        for prog_idx, program in enumerate(sorted(programs, key=lambda p: p.priority)):
            linked = self.archive.list_program_targets(program.id)
            if not linked:
                continue

            cfg = None
            if program.default_instrument_config_id:
                cfg = self.archive.get_instrument_config(program.default_instrument_config_id)
            equip_ok, equip_reason = validate_instrument_config(cfg, equipment)

            # Default: full night window; slight stagger for conflict resolution demos
            w_start, w_end = start_utc, end_utc
            if prog_idx > 0:
                w_start, w_end = _shift_window(start_utc, end_utc, 0.0)  # same window -> conflict

            for target, _role, _so in linked:
                if target.ra_deg is None or target.dec_deg is None:
                    blocks.append(
                        ObservationBlock(
                            id=new_id(),
                            daily_plan_id=plan.id,
                            program_id=program.id,
                            target_id=target.id,
                            instrument_config_id=cfg.id if cfg else None,
                            sort_order=sort_order,
                            window_start_utc=w_start,
                            window_end_utc=w_end,
                            status="inviavel_ceu",
                            status_reason="alvo sem coordenadas RA/Dec",
                            priority=program.priority,
                            technique=None,
                            meteo_snapshot_id=meteo_snap.id,
                        )
                    )
                    sort_order += 1
                    continue

                eph = self.ephemeris.altitude_azimuth(
                    ra_deg=target.ra_deg,
                    dec_deg=target.dec_deg,
                    latitude_deg=site.latitude_deg,
                    longitude_deg=site.longitude_deg,
                    elevation_m=site.elevation_m,
                    utc_iso=mid_utc,
                )
                eph_snap = self.archive.save_ephemeris_snapshot(
                    EphemerisSnapshot(
                        id=new_id(),
                        workspace_id=workspace_id,
                        site_id=site_id,
                        target_id=target.id,
                        epoch_utc=mid_utc,
                        source="astropy",
                        payload=eph,
                    )
                )

                status = "agendado"
                reason: str | None = None
                alt = float(eph["alt_deg"])
                if alt < site.min_altitude_deg:
                    status = "inviavel_ceu"
                    reason = f"altitude {alt:.1f} deg < min {site.min_altitude_deg} deg"
                elif not meteo_ok:
                    status = "inviavel_meteo"
                    reason = meteo_reason
                elif not equip_ok:
                    status = "inviavel_equip"
                    reason = equip_reason

                tmpl = self.archive.get_program_template(program.template_id)
                technique = tmpl.technique if tmpl else None

                blocks.append(
                    ObservationBlock(
                        id=new_id(),
                        daily_plan_id=plan.id,
                        program_id=program.id,
                        target_id=target.id,
                        instrument_config_id=cfg.id if cfg else None,
                        sort_order=sort_order,
                        window_start_utc=w_start,
                        window_end_utc=w_end,
                        predicted_altitude_deg=alt,
                        airmass=eph.get("airmass"),
                        status=status,  # type: ignore[arg-type]
                        status_reason=reason,
                        priority=program.priority,
                        technique=technique,
                        ephemeris_snapshot_id=eph_snap.id,
                        meteo_snapshot_id=meteo_snap.id,
                    )
                )
                sort_order += 1

        resolve_priority_conflicts(blocks)
        self.archive.replace_observation_blocks(plan.id, blocks)
        return plan
