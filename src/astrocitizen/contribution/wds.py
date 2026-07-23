"""Export medida WDS / USNO (PO-G01 / EXP-WDS)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID

from astrocitizen.shared.errors import DomainError


def _fmt_mag(val: Any) -> str:
    if val is None or val == "":
        return "na"
    try:
        return f"{float(val):.2f}"
    except (TypeError, ValueError):
        return "na"


def format_wds_measure(
    *,
    object_name: str,
    epoch_utc: str,
    pa_deg: float,
    sep_arcsec: float,
    method: str = "micrometer",
    mag_primary: float | None = None,
    mag_secondary: float | None = None,
    observer: str = "AstroCitizen",
    observatory: str = "",
    discoverer: str = "",
    notes: str = "",
) -> str:
    """Texto estruturado EXP-WDS para contribuicao manual USNO."""
    obj = (object_name or "").strip()
    epoch = (epoch_utc or "").strip()
    meth = (method or "micrometer").strip() or "micrometer"
    obs = (observer or "AstroCitizen").strip() or "AstroCitizen"
    site = (observatory or "").strip() or "na"
    mag1 = _fmt_mag(mag_primary)
    mag2 = _fmt_mag(mag_secondary)
    lines = [
        "#TYPE=ASTROCITIZEN_WDS",
        "#FORMAT=EXP-WDS measure",
        "#SOFTWARE=AstroCitizen/0.0.1",
        f"#WDS={obj}",
        f"#EPOCH_UTC={epoch}",
        f"#PA_DEG={float(pa_deg):.3f}",
        f"#SEP_ARCSEC={float(sep_arcsec):.3f}",
        f"#MAG1={mag1}",
        f"#MAG2={mag2}",
        f"#METHOD={meth}",
        f"#OBSERVER={obs}",
        f"#OBSERVATORY={site}",
    ]
    if discoverer:
        lines.append(f"#DISCOVERER={discoverer.strip()}")
    if notes:
        lines.append(f"#NOTES={notes.strip()[:500]}")
    lines.extend(
        [
            "#",
            "# wds,epoch_utc,pa_deg,sep_arcsec,mag1,mag2,method,observer,observatory",
            (
                f"{obj},{epoch},{float(pa_deg):.3f},{float(sep_arcsec):.3f},"
                f"{mag1},{mag2},{meth},{obs},{site}"
            ),
            "#SUBMIT=manual USNO / WDS maintainer (confirmar procedimento vigente)",
        ]
    )
    return "\n".join(lines) + "\n"


def format_wds_csv_line(
    *,
    object_name: str,
    epoch_utc: str,
    pa_deg: float,
    sep_arcsec: float,
    method: str = "micrometer",
    mag_primary: float | None = None,
    mag_secondary: float | None = None,
    observer: str = "AstroCitizen",
    observatory: str = "",
) -> str:
    header = "wds,epoch_utc,pa_deg,sep_arcsec,mag1,mag2,method,observer,observatory"
    row = (
        f"{object_name.strip()},{epoch_utc.strip()},{float(pa_deg):.3f},"
        f"{float(sep_arcsec):.3f},{_fmt_mag(mag_primary)},{_fmt_mag(mag_secondary)},"
        f"{(method or 'micrometer').strip()},"
        f"{(observer or 'AstroCitizen').strip()},"
        f"{(observatory or '').strip() or 'na'}"
    )
    return header + "\n" + row + "\n"


def fields_from_double_product(
    archive: Any,
    product: Any,
    *,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Extrai campos EXP-WDS de AnalysisProduct double_measure."""
    params = dict(getattr(product, "parameters", None) or {})
    summary = dict(getattr(product, "summary", None) or {})
    over = dict(overrides or {})
    observatory = str(over.get("observatory") or "").strip()
    if not observatory:
        sid = params.get("site_id")
        if sid and hasattr(archive, "get_site"):
            try:
                site = archive.get_site(UUID(str(sid)))
            except (TypeError, ValueError):
                site = None
            if site is not None:
                observatory = str(getattr(site, "name", "") or "")
    return {
        "object_name": str(
            over.get("object_name")
            or over.get("object")
            or summary.get("object")
            or params.get("object_name")
            or ""
        ).strip(),
        "epoch_utc": str(
            over.get("epoch_utc") or summary.get("epoch_utc") or params.get("epoch_utc") or ""
        ).strip(),
        "pa_deg": float(
            over["pa_deg"]
            if over.get("pa_deg") is not None
            else summary.get("pa_deg")
            if summary.get("pa_deg") is not None
            else params.get("pa_deg")
            or 0.0
        ),
        "sep_arcsec": float(
            over["sep_arcsec"]
            if over.get("sep_arcsec") is not None
            else summary.get("sep_arcsec")
            if summary.get("sep_arcsec") is not None
            else params.get("sep_arcsec")
            or 0.0
        ),
        "method": str(
            over.get("method") or summary.get("method") or params.get("method") or "micrometer"
        ).strip()
        or "micrometer",
        "mag_primary": (
            over["mag_primary"]
            if over.get("mag_primary") is not None
            else params.get("mag_primary")
        ),
        "mag_secondary": (
            over["mag_secondary"]
            if over.get("mag_secondary") is not None
            else params.get("mag_secondary")
        ),
        "observer": str(
            over.get("observer")
            or summary.get("observer")
            or params.get("observer")
            or "AstroCitizen"
        ).strip()
        or "AstroCitizen",
        "observatory": observatory,
        "discoverer": str(over.get("discoverer") or params.get("discoverer") or "").strip(),
        "notes": str(over.get("notes") or params.get("notes") or "").strip(),
    }


class ExportWds:
    """Gera ficheiro EXP-WDS a partir de produto double_measure."""

    def __init__(self, archive: Any) -> None:
        self.archive = archive

    def execute(
        self,
        *,
        product_id: UUID,
        out_path: Path,
        overrides: dict[str, Any] | None = None,
        write_csv: bool = True,
    ) -> Path:
        product = self.archive.get_analysis_product(product_id)
        if product is None:
            raise DomainError(f"produto nao encontrado: {product_id}")
        if product.product_type != "double_measure":
            raise DomainError(f"produto nao e double_measure: {product.product_type}")
        fields = fields_from_double_product(self.archive, product, overrides=overrides)
        if not fields["object_name"]:
            raise DomainError("object_name / WDS id obrigatorio")
        if not fields["epoch_utc"]:
            raise DomainError("epoch_utc obrigatoria")
        text = format_wds_measure(**fields)
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
        if write_csv:
            csv_path = out_path.with_suffix(".csv")
            csv_path.write_text(
                format_wds_csv_line(
                    object_name=fields["object_name"],
                    epoch_utc=fields["epoch_utc"],
                    pa_deg=fields["pa_deg"],
                    sep_arcsec=fields["sep_arcsec"],
                    method=fields["method"],
                    mag_primary=fields["mag_primary"],
                    mag_secondary=fields["mag_secondary"],
                    observer=fields["observer"],
                    observatory=fields["observatory"],
                ),
                encoding="utf-8",
            )
        return out_path
