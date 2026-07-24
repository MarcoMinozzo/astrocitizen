"""Provider AAVSO — wrapper sobre contribution + VSX (D-012 / AC-096)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID

from astrocitizen.adapters.aavso_portal import WEBOBS_URL
from astrocitizen.adapters.sky.vsx_resolver import VsxResolver
from astrocitizen.contribution.aavso import ExportAavso, format_aavso_extended
from astrocitizen.domain.observation import Observation
from astrocitizen.integrations.base import BaseObservatoryProvider
from astrocitizen.shared.errors import DomainError


class AavsoProvider(BaseObservatoryProvider):
    name = "aavso"
    features = frozenset({"search", "prepare_photometry"})

    def __init__(self, archive: Any | None = None) -> None:
        self.archive = archive
        self.webobs_url = WEBOBS_URL

    def search_object(self, name: str) -> dict[str, Any]:
        return VsxResolver().resolve(name)

    def prepare_photometry(
        self, observation: Observation, *, out_path: Path, **kwargs: Any
    ) -> Path:
        """Gera AEF. Preferir `product_id` + archive; fallback pontos em extra."""
        product_id = kwargs.get("product_id") or observation.extra.get("product_id")
        band = str(kwargs.get("band") or observation.filter_name or "V")
        chart = str(kwargs.get("chart") or "NA")
        star = observation.object_name
        obscode = observation.observatory_code or kwargs.get("obscode")
        if not obscode:
            raise DomainError("AAVSO: observatory_code / obscode obrigatorio", rule_id="D-012")

        if product_id is not None and self.archive is not None:
            pid = product_id if isinstance(product_id, UUID) else UUID(str(product_id))
            return ExportAavso(self.archive).execute(
                product_id=pid,
                star_name=star,
                observer_code=str(obscode),
                out_path=Path(out_path),
                band=band,
                chart=chart,
            )

        points = list(observation.extra.get("points") or [])
        if observation.mag is not None and observation.jd is not None:
            points = [
                {
                    "t_utc": observation.extra.get("t_utc"),
                    "y": observation.mag,
                    "y_err": observation.mag_err,
                }
            ]
            # JD-only points: synthesize ISO if missing — format needs t_utc
            if not points[0].get("t_utc"):
                raise DomainError(
                    "AAVSO: indique product_id ou points com t_utc em Observation.extra",
                    rule_id="D-012",
                )
        if not points:
            raise DomainError(
                "AAVSO: product_id+archive ou Observation.extra['points']",
                rule_id="D-012",
            )
        text = format_aavso_extended(
            star_name=star,
            observer_code=str(obscode),
            points=points,
            band=band,
            chart=chart,
        )
        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        return out
