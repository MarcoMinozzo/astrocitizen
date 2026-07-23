"""Export AAVSO Extended Format (AC-093 / AC-096) — JD via Astropy."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID

from astropy.time import Time

from astrocitizen.shared.errors import DomainError, NotFoundError


def _to_jd(t_utc: str | None) -> float | None:
    if not t_utc:
        return None
    try:
        return float(Time(t_utc, format="isot", scale="utc").jd)
    except Exception:
        try:
            return float(Time(t_utc, format="iso", scale="utc").jd)
        except Exception:
            return None


def format_aavso_extended(
    *,
    star_name: str,
    observer_code: str,
    points: list[dict],
    band: str = "V",
    chart: str = "NA",
) -> str:
    """Gera texto AAVSO Extended (uma linha por medida, DATE=JD)."""
    lines = [
        "#TYPE=EXTENDED",
        f"#OBSCODE={observer_code}",
        "#SOFTWARE=AstroCitizen/0.0.1",
        "#DELIM=,",
        "#DATE=JD",
        "#OBSTYPE=CCD",
        "#",
    ]
    n_data = 0
    for pt in points:
        mag = pt.get("y")
        if mag is None:
            continue
        try:
            mag_f = float(mag)
        except (TypeError, ValueError):
            continue
        jd = _to_jd(pt.get("t_utc"))
        if jd is None:
            continue
        merr = pt.get("y_err")
        merr_s = f"{float(merr):.4f}" if merr is not None else "na"
        notes = str(pt.get("t_utc") or "")
        lines.append(
            f"{star_name},{jd:.6f},{mag_f:.4f},{merr_s},{band},"
            f"NO,STD,ENSEMBLE,na,na,na,na,{chart},{notes}"
        )
        n_data += 1
    if n_data == 0:
        raise DomainError(
            "nenhum ponto com t_utc parseavel e magnitude numerica para AEF",
            rule_id="AC-096",
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
        chart: str = "NA",
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
            chart=chart or "NA",
        )
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
        return out_path
