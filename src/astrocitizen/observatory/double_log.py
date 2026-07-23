"""Medida de estrelas duplas (PO-G01 / IN-LOG) — PA + sep + epoch."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID

from astrocitizen.adapters.fs import LocalArtifactStore
from astrocitizen.reduction.models import AnalysisProduct
from astrocitizen.shared.errors import DomainError
from astrocitizen.shared.ids import new_id
from astrocitizen.shared.timeutil import utc_now_iso

VALID_METHODS = ("micrometer", "imaging_manual", "other")


class LogDoubleMeasure:
    """Regista medida de dupla: Observation + AnalysisProduct double_measure."""

    def __init__(
        self, archive: Any, store: LocalArtifactStore | None = None
    ) -> None:
        self.archive = archive
        self.store = store

    def execute(
        self,
        *,
        workspace_id: UUID,
        object_name: str,
        pa_deg: float,
        sep_arcsec: float,
        epoch_utc: str | None = None,
        method: str = "micrometer",
        mag_primary: float | None = None,
        mag_secondary: float | None = None,
        notes: str = "",
        image_path: Path | None = None,
        site_id: UUID | None = None,
        program_id: UUID | None = None,
        target_id: UUID | None = None,
        observer: str = "AstroCitizen",
    ) -> AnalysisProduct:
        obj = (object_name or "").strip()
        if not obj:
            raise DomainError("object_name obrigatorio")
        try:
            pa = float(pa_deg)
            sep = float(sep_arcsec)
        except (TypeError, ValueError) as exc:
            raise DomainError("pa_deg e sep_arcsec devem ser numericos") from exc
        if not (0.0 <= pa < 360.0):
            raise DomainError("pa_deg deve estar em [0, 360)")
        if sep <= 0.0:
            raise DomainError("sep_arcsec deve ser > 0")
        meth = (method or "micrometer").strip().lower()
        if meth not in VALID_METHODS:
            raise DomainError(
                f"method invalido: {method} ({', '.join(VALID_METHODS)})"
            )

        when = (epoch_utc or "").strip() or utc_now_iso()
        if target_id is not None:
            tgt = self.archive.get_target(target_id)
            if tgt is None:
                raise DomainError(f"alvo nao encontrado: {target_id}")

        image_uri = None
        channel = "IN-LOG"
        if image_path is not None:
            path = Path(image_path)
            if not path.is_file():
                raise DomainError(f"imagem nao encontrada: {path}")
            if self.store is None:
                raise DomainError("store obrigatorio quando ha image_path")
            image_uri = self.store.put(path, key=f"import/double/{path.name}")
            channel = "IN-IMP"

        obs_id = new_id()
        obs_notes = f"double:{obj} PA={pa:.2f} sep={sep:.3f}\""
        if notes:
            obs_notes = f"{obs_notes} | {notes[:200]}"
        self.archive.create_observation(
            observation_id=obs_id,
            workspace_id=workspace_id,
            observed_at_utc=when,
            site_id=site_id,
            program_id=program_id,
            simulated=False,
            notes=obs_notes,
        )
        if image_uri:
            self.archive.save_artifact(
                artifact_id=new_id(),
                workspace_id=workspace_id,
                kind="double_image",
                uri=image_uri,
                filename=Path(image_path).name if image_path else "image",
                observation_id=obs_id,
                size_bytes=Path(image_path).stat().st_size if image_path else 0,
            )

        product = AnalysisProduct(
            id=new_id(),
            workspace_id=workspace_id,
            program_id=program_id,
            product_type="double_measure",
            version_num=1,
            is_publishable=False,
            parameters={
                "channel": channel,
                "template": "PO-G01",
                "object_name": obj,
                "pa_deg": pa,
                "sep_arcsec": sep,
                "epoch_utc": when,
                "method": meth,
                "mag_primary": mag_primary,
                "mag_secondary": mag_secondary,
                "notes": notes,
                "observer": observer,
                "image_uri": image_uri,
                "target_id": str(target_id) if target_id else None,
                "site_id": str(site_id) if site_id else None,
                "observation_id": str(obs_id),
            },
            summary={
                "object": obj,
                "pa_deg": pa,
                "sep_arcsec": sep,
                "epoch_utc": when,
                "method": meth,
                "observer": observer,
                "has_image": image_uri is not None,
            },
            state="ready",
        )
        product = self.archive.save_analysis_product(product)
        self.archive.link_product_observation(product.id, obs_id)
        self.archive.save_measurement_points(
            product.id,
            [
                {
                    "id": str(new_id()),
                    "t_utc": when,
                    "sequence_index": 0,
                    "x": pa,
                    "y": sep,
                    "y_err": None,
                    "band": "double",
                    "meta": {
                        "pa_deg": pa,
                        "sep_arcsec": sep,
                        "object": obj,
                        "method": meth,
                    },
                }
            ],
        )
        return product
