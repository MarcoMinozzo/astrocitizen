"""Export ExoClock light curve (PO-A05)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import UUID

from astropy.time import Time

from astrocitizen.shared.errors import NotFoundError


def _to_bjd_tdb(t_utc: str | None) -> float | None:
    """Aproxima BJD_TDB ~= JD(TDB); suficiente para MVP de formato."""
    if not t_utc:
        return None
    try:
        return float(Time(t_utc, format="isot", scale="utc").tdb.jd)
    except Exception:
        try:
            return float(Time(t_utc, format="iso", scale="utc").tdb.jd)
        except Exception:
            return None


def format_exoclock_lc(
    *,
    target: str,
    points: list[dict],
    telescope: str = "AstroCitizen",
    observer: str = "AstroCitizen",
) -> str:
    """Texto estilo subset AIJ/HOPS: BJD_TDB flux flux_err airmass."""
    lines = [
        "# AstroCitizen ExoClock export",
        f"# TARGET={target}",
        f"# TELESCOPE={telescope}",
        f"# OBSERVER={observer}",
        "# UPLOAD=https://www.exoclock.space/upload/",
        "# columns: BJD_TDB flux flux_err airmass",
    ]
    for pt in points:
        bjd = _to_bjd_tdb(pt.get("t_utc"))
        flux = pt.get("y")
        if bjd is None or flux is None:
            continue
        err = pt.get("y_err")
        err_s = f"{float(err):.6f}" if err is not None else "nan"
        meta = pt.get("meta") or {}
        if isinstance(meta, str):
            airmass = "nan"
        else:
            am = meta.get("airmass")
            airmass = f"{float(am):.4f}" if am is not None else "nan"
        lines.append(f"{bjd:.8f} {float(flux):.8f} {err_s} {airmass}")
    return "\n".join(lines) + "\n"


class ExportExoclock:
    def __init__(self, archive: Any) -> None:
        self.archive = archive

    def execute(
        self,
        *,
        product_id: UUID,
        target: str,
        out_path: Path,
        telescope: str = "AstroCitizen",
        observer: str = "AstroCitizen",
    ) -> Path:
        product = self.archive.get_analysis_product(product_id)
        if product is None:
            raise NotFoundError(f"produto nao encontrado: {product_id}")
        points = self.archive.list_measurement_points(product_id)
        if not points:
            raise NotFoundError("produto sem measurement_points")
        norm: list[dict] = []
        for p in points:
            row = dict(p)
            meta = row.get("meta")
            if isinstance(meta, str):
                try:
                    row["meta"] = json.loads(meta)
                except json.JSONDecodeError:
                    row["meta"] = {}
            norm.append(row)
        text = format_exoclock_lc(
            target=target,
            points=norm,
            telescope=telescope,
            observer=observer,
        )
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
        return out_path
