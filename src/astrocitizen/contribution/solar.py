"""Export relatorio solar amador (PO-E03 / redes solares)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID

from astrocitizen.shared.errors import DomainError


def format_solar_report(
    *,
    observer: str,
    epoch_utc: str,
    groups: int,
    spots: int,
    wolf_r: float,
    filter_name: str = "white-light",
    site: str | None = None,
    notes: str | None = None,
) -> str:
    """Texto simples alinhado a contagens diarias (SILSO-like / arquivo local)."""
    lines = [
        "#TYPE=ASTROCITIZEN_SOLAR",
        "#FORMAT=PO-E03 sunspot count",
        f"#OBSERVER={observer}",
        f"#DATE-OBS={epoch_utc}",
        f"#FILTER={filter_name}",
    ]
    if site:
        lines.append(f"#SITE={site}")
    lines.extend(
        [
            "#",
            "# groups spots wolf_r",
            f"{int(groups)} {int(spots)} {float(wolf_r):.2f}",
        ]
    )
    if notes:
        lines.append(f"#NOTE={notes}")
    lines.append("#SAFETY=filter_confirmed;no_unfiltered_eyepiece;daytime_ack")
    return "\n".join(lines) + "\n"


class ExportSolarReport:
    """Gera ficheiro de contagem a partir de produto solar_sunspots."""

    def __init__(self, archive: Any) -> None:
        self.archive = archive

    def execute(
        self,
        *,
        product_id: UUID,
        out_path: Path,
        observer: str | None = None,
        site: str | None = None,
        notes: str | None = None,
    ) -> Path:
        product = self.archive.get_analysis_product(product_id)
        if product is None:
            raise DomainError(f"produto nao encontrado: {product_id}")
        if product.product_type != "solar_sunspots":
            raise DomainError(f"produto nao e solar_sunspots: {product.product_type}")
        obs = observer or str(product.parameters.get("observer") or "AstroCitizen")
        text = format_solar_report(
            observer=obs,
            epoch_utc=str(product.summary.get("epoch_utc") or ""),
            groups=int(product.summary.get("groups") or 0),
            spots=int(product.summary.get("spots") or 0),
            wolf_r=float(product.summary.get("wolf_r") or 0.0),
            filter_name=str(product.summary.get("filter_name") or "white-light"),
            site=site,
            notes=notes,
        )
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
        return out_path
