"""Log visual (PO-F03 / IN-LOG) — observacao sem CCD."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from astrocitizen.reduction.models import AnalysisProduct
from astrocitizen.shared.errors import DomainError
from astrocitizen.shared.ids import new_id
from astrocitizen.shared.timeutil import utc_now_iso


class LogVisualObservation:
    """Regista entrada visual: Observation + AnalysisProduct visual_log."""

    def __init__(self, archive: Any) -> None:
        self.archive = archive

    def execute(
        self,
        *,
        workspace_id: UUID,
        object_name: str,
        description: str,
        conditions: str = "",
        site_id: UUID | None = None,
        program_id: UUID | None = None,
        target_id: UUID | None = None,
        observer: str = "AstroCitizen",
        observed_at_utc: str | None = None,
        magnitude: float | None = None,
        seeing: str | None = None,
    ) -> AnalysisProduct:
        obj = (object_name or "").strip()
        desc = (description or "").strip()
        if not obj:
            raise DomainError("object_name obrigatorio")
        if not desc:
            raise DomainError("description obrigatoria")

        when = observed_at_utc or utc_now_iso()
        if target_id is not None:
            tgt = self.archive.get_target(target_id)
            if tgt is None:
                raise DomainError(f"alvo nao encontrado: {target_id}")
            if not obj:
                obj = tgt.designation

        obs_id = new_id()
        notes = f"visual:{obj}"
        if conditions:
            notes = f"{notes} | {conditions[:200]}"
        self.archive.create_observation(
            observation_id=obs_id,
            workspace_id=workspace_id,
            observed_at_utc=when,
            site_id=site_id,
            program_id=program_id,
            simulated=False,
            notes=notes,
        )

        product = AnalysisProduct(
            id=new_id(),
            workspace_id=workspace_id,
            program_id=program_id,
            product_type="visual_log",
            version_num=1,
            is_publishable=False,
            parameters={
                "channel": "IN-LOG",
                "object_name": obj,
                "description": desc,
                "conditions": conditions,
                "observer": observer,
                "seeing": seeing,
                "magnitude": magnitude,
                "target_id": str(target_id) if target_id else None,
                "site_id": str(site_id) if site_id else None,
                "observation_id": str(obs_id),
            },
            summary={
                "object": obj,
                "observed_at_utc": when,
                "observer": observer,
                "has_magnitude": magnitude is not None,
                "conditions": (conditions or "")[:80],
            },
            state="ready",
        )
        product = self.archive.save_analysis_product(product)
        self.archive.link_product_observation(product.id, obs_id)
        return product
