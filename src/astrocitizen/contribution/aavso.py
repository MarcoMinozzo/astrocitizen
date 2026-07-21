"""Export AAVSO Extended Format (simplificado  AC-093 inicio)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID

from astrocitizen.shared.errors import NotFoundError
from astrocitizen.shared.timeutil import utc_now_iso


def format_aavso_extended(
    *,
    star_name: str,
    observer_code: str,
    points: list[dict],
    band: str = "V",
    chart: str = "NA",
) -> str:
    """Gera texto AAVSO Extended (uma linha por medida)."""
    lines = [
        "#TYPE=EXTENDED",
        f"#OBSCODE={observer_code}",
        f"#SOFTWARE=AstroCitizen/0.0.1",
        f"#DELIM=,",
        f"#DATE={utc_now_iso()}",
        f"#NAME={star_name}",
        "#OBSTYPE=CCD",
        "#",
    ]
    for pt in points:
        # JD approx from ISO not implemented fully  use DATE-OBS string as NOTES for MVP
        # AAVSO wants JD; store placeholder MAG and use t_utc in NOTES
        mag = pt.get("y")
        if mag is None:
            continue
        t = pt.get("t_utc") or ""
        # Simplified: MAG,MERR,FILT,TRANS,MTYPE,CNAME,CMAG,KNAME,KMAG,AIRMASS,GROUP,CHART,NOTES
        merr = pt.get("y_err") if pt.get("y_err") is not None else "na"
        lines.append(
            f"{star_name},na,{mag:.4f},{merr},{band},NO,STD,ENSEMBLE,na,na,na,na,{chart},t={t}"
        )
    return "\n".join(lines) + "\n"


class ExportAavso:
    def __init__(self, archive: Any) -> None:
        self.archive = archive

    def execute(
        self,
        *,
        product_id: UUID,
        star_name: str,
        observer_code: str,
        out_path: Path,
        band: str = "V",
    ) -> Path:
        product = self.archive.get_analysis_product(product_id)
        if product is None:
            raise NotFoundError(f"produto nao encontrado: {product_id}")
        points = self.archive.list_measurement_points(product_id)
        if not points:
            raise NotFoundError("produto sem measurement_points")
        text = format_aavso_extended(
            star_name=star_name,
            observer_code=observer_code,
            points=points,
            band=band or (points[0].get("band") or "V"),
        )
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
        return out_path
