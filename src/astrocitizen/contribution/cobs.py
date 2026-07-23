"""Export observacao de cometa COBS / ICQ (PO-A10 / EXP-COBS-ICQ)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from astrocitizen.shared.errors import DomainError


def utc_to_icq_date(epoch_utc: str) -> str:
    """Converte ISO UTC para ICQ YYYY MM DD.DD (fraccao de dia 0.01)."""
    text = (epoch_utc or "").strip()
    if not text:
        return ""
    # Already ICQ-like
    parts = text.replace("-", " ").split()
    if len(parts) >= 3 and "." in parts[2] and len(parts[0]) == 4:
        try:
            float(parts[2])
            return f"{parts[0]} {parts[1].zfill(2)} {float(parts[2]):05.2f}"
        except ValueError:
            pass
    raw = text.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise DomainError(f"epoch UTC invalida: {epoch_utc}") from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    day_frac = (
        dt.hour / 24.0
        + dt.minute / 1440.0
        + dt.second / 86400.0
        + dt.microsecond / 86400_000_000.0
    )
    day = dt.day + day_frac
    return f"{dt.year:04d} {dt.month:02d} {day:05.2f}"


def _fmt_opt(val: Any, *, decimals: int | None = None) -> str:
    if val is None or val == "":
        return ""
    if decimals is None:
        return str(val).strip()
    try:
        return f"{float(val):.{decimals}f}"
    except (TypeError, ValueError):
        return str(val).strip()


def format_cobs_measure(
    *,
    designation: str,
    epoch_utc: str,
    mag: float,
    mag_method: str = "B",
    comp_cat: str = "",
    aperture_cm: float | None = None,
    instr_type: str = "L",
    focal_ratio: float | None = None,
    power_or_exptime: float | None = None,
    coma_arcmin: float | None = None,
    dc: str = "",
    tail_deg: float | None = None,
    tail_pa: float | None = None,
    obscode: str = "",
    observer: str = "AstroCitizen",
    location: str = "",
    notes: str = "",
) -> str:
    """Texto estruturado EXP-COBS-ICQ para contribuicao manual COBS."""
    desig = (designation or "").strip()
    epoch = (epoch_utc or "").strip()
    ut_date = utc_to_icq_date(epoch) if epoch and "T" in epoch else epoch
    if epoch and not ut_date:
        ut_date = utc_to_icq_date(epoch)
    method = (mag_method or "B").strip()[:1].upper() or "B"
    obs = (observer or "AstroCitizen").strip() or "AstroCitizen"
    code = (obscode or "").strip()
    lines = [
        "#TYPE=ASTROCITIZEN_COBS",
        "#FORMAT=EXP-COBS-ICQ",
        "#SOFTWARE=AstroCitizen/0.0.1",
        f"#DESIGNATION={desig}",
        f"#EPOCH_UTC={epoch}",
        f"#UT_DATE={ut_date}",
        f"#MAG={float(mag):.1f}",
        f"#MAG_METHOD={method}",
        f"#COMP_CAT={(comp_cat or '').strip() or 'na'}",
        f"#APERTURE_CM={_fmt_opt(aperture_cm, decimals=1) or 'na'}",
        f"#INSTR_TYPE={(instr_type or 'L').strip()[:1].upper() or 'L'}",
        f"#FOCAL_RATIO={_fmt_opt(focal_ratio, decimals=0) or 'na'}",
        f"#POWER_OR_EXPTIME={_fmt_opt(power_or_exptime, decimals=0) or 'na'}",
        f"#COMA_ARCMIN={_fmt_opt(coma_arcmin, decimals=1) or 'na'}",
        f"#DC={(dc or '').strip() or 'na'}",
        f"#TAIL_DEG={_fmt_opt(tail_deg, decimals=1) or 'na'}",
        f"#TAIL_PA={_fmt_opt(tail_pa, decimals=0) or 'na'}",
        f"#OBSCODE={code or 'na'}",
        f"#OBSERVER={obs}",
        f"#LOCATION={(location or '').strip() or 'na'}",
    ]
    if notes:
        lines.append(f"#NOTES={notes.strip()[:500]}")
    csv_row = (
        f"{desig},{ut_date},{float(mag):.1f},{method},"
        f"{(comp_cat or '').strip() or 'na'},"
        f"{_fmt_opt(aperture_cm, decimals=1) or 'na'},"
        f"{(instr_type or 'L').strip()[:1].upper() or 'L'},"
        f"{_fmt_opt(focal_ratio, decimals=0) or 'na'},"
        f"{_fmt_opt(power_or_exptime, decimals=0) or 'na'},"
        f"{_fmt_opt(coma_arcmin, decimals=1) or 'na'},"
        f"{(dc or '').strip() or 'na'},"
        f"{_fmt_opt(tail_deg, decimals=1) or 'na'},"
        f"{_fmt_opt(tail_pa, decimals=0) or 'na'},"
        f"{code or 'na'},{obs},{(location or '').strip() or 'na'}"
    )
    lines.extend(
        [
            "#",
            (
                "# designation,ut_date,mag,mag_method,comp_cat,aperture_cm,instr_type,"
                "focal_ratio,power_or_exptime,coma_arcmin,dc,tail_deg,tail_pa,"
                "obscode,observer,location"
            ),
            csv_row,
            "#SUBMIT=manual https://www.cobs.si/",
            "#ICQ_HELP=https://www.cobs.si/help/icq_format/",
        ]
    )
    return "\n".join(lines) + "\n"


def format_cobs_csv(
    *,
    designation: str,
    epoch_utc: str,
    mag: float,
    mag_method: str = "B",
    comp_cat: str = "",
    aperture_cm: float | None = None,
    instr_type: str = "L",
    focal_ratio: float | None = None,
    power_or_exptime: float | None = None,
    coma_arcmin: float | None = None,
    dc: str = "",
    tail_deg: float | None = None,
    tail_pa: float | None = None,
    obscode: str = "",
    observer: str = "AstroCitizen",
    location: str = "",
) -> str:
    ut_date = epoch_utc
    if epoch_utc and "T" in epoch_utc:
        ut_date = utc_to_icq_date(epoch_utc)
    header = (
        "designation,ut_date,mag,mag_method,comp_cat,aperture_cm,instr_type,"
        "focal_ratio,power_or_exptime,coma_arcmin,dc,tail_deg,tail_pa,"
        "obscode,observer,location"
    )
    row = (
        f"{designation.strip()},{ut_date},{float(mag):.1f},"
        f"{(mag_method or 'B').strip()[:1].upper() or 'B'},"
        f"{(comp_cat or '').strip() or 'na'},"
        f"{_fmt_opt(aperture_cm, decimals=1) or 'na'},"
        f"{(instr_type or 'L').strip()[:1].upper() or 'L'},"
        f"{_fmt_opt(focal_ratio, decimals=0) or 'na'},"
        f"{_fmt_opt(power_or_exptime, decimals=0) or 'na'},"
        f"{_fmt_opt(coma_arcmin, decimals=1) or 'na'},"
        f"{(dc or '').strip() or 'na'},"
        f"{_fmt_opt(tail_deg, decimals=1) or 'na'},"
        f"{_fmt_opt(tail_pa, decimals=0) or 'na'},"
        f"{(obscode or '').strip() or 'na'},"
        f"{(observer or 'AstroCitizen').strip()},"
        f"{(location or '').strip() or 'na'}"
    )
    return header + "\n" + row + "\n"


def fields_from_comet_context(
    archive: Any,
    product: Any | None,
    *,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Monta campos EXP-COBS a partir de visual_log / light_curve + overrides."""
    over = dict(overrides or {})
    params: dict[str, Any] = {}
    summary: dict[str, Any] = {}
    if product is not None:
        params = dict(getattr(product, "parameters", None) or {})
        summary = dict(getattr(product, "summary", None) or {})

    designation = str(
        over.get("designation")
        or summary.get("object")
        or params.get("object_name")
        or params.get("designation")
        or params.get("target")
        or ""
    ).strip()
    epoch = str(
        over.get("epoch_utc")
        or over.get("ut_date")
        or summary.get("observed_at_utc")
        or summary.get("epoch_utc")
        or params.get("observed_at_utc")
        or ""
    ).strip()
    mag = over.get("mag")
    if mag is None:
        mag = params.get("magnitude")
    if mag is None:
        mag = summary.get("mag")
    if mag is None and product is not None and hasattr(archive, "list_measurement_points"):
        points = archive.list_measurement_points(product.id)
        if points:
            last = points[-1]
            mag = last.get("y")
            if not epoch:
                epoch = str(last.get("t_utc") or "").strip()

    location = str(over.get("location") or "").strip()
    if not location and params.get("site_id") and hasattr(archive, "get_site"):
        try:
            site = archive.get_site(UUID(str(params["site_id"])))
        except (TypeError, ValueError):
            site = None
        if site is not None:
            location = str(getattr(site, "name", "") or "")

    return {
        "designation": designation,
        "epoch_utc": epoch,
        "mag": float(mag) if mag is not None else None,
        "mag_method": str(over.get("mag_method") or params.get("mag_method") or "B").strip()
        or "B",
        "comp_cat": str(over.get("comp_cat") or params.get("comp_cat") or "").strip(),
        "aperture_cm": (
            over["aperture_cm"]
            if over.get("aperture_cm") is not None
            else params.get("aperture_cm")
        ),
        "instr_type": str(over.get("instr_type") or params.get("instr_type") or "L").strip()
        or "L",
        "focal_ratio": (
            over["focal_ratio"]
            if over.get("focal_ratio") is not None
            else params.get("focal_ratio")
        ),
        "power_or_exptime": (
            over["power_or_exptime"]
            if over.get("power_or_exptime") is not None
            else params.get("power_or_exptime")
        ),
        "coma_arcmin": (
            over["coma_arcmin"]
            if over.get("coma_arcmin") is not None
            else params.get("coma_arcmin")
        ),
        "dc": str(over.get("dc") if over.get("dc") is not None else params.get("dc") or "").strip(),
        "tail_deg": (
            over["tail_deg"] if over.get("tail_deg") is not None else params.get("tail_deg")
        ),
        "tail_pa": (
            over["tail_pa"] if over.get("tail_pa") is not None else params.get("tail_pa")
        ),
        "obscode": str(over.get("obscode") or params.get("obscode") or "").strip(),
        "observer": str(
            over.get("observer")
            or summary.get("observer")
            or params.get("observer")
            or "AstroCitizen"
        ).strip()
        or "AstroCitizen",
        "location": location,
        "notes": str(
            over.get("notes") or params.get("description") or params.get("notes") or ""
        ).strip(),
    }


class ExportCobs:
    """Gera ficheiro EXP-COBS-ICQ (produto opcional + overrides)."""

    def __init__(self, archive: Any) -> None:
        self.archive = archive

    def execute(
        self,
        *,
        out_path: Path,
        product_id: UUID | None = None,
        overrides: dict[str, Any] | None = None,
        write_csv: bool = True,
    ) -> Path:
        product = None
        if product_id is not None:
            product = self.archive.get_analysis_product(product_id)
            if product is None:
                raise DomainError(f"produto nao encontrado: {product_id}")
            if product.product_type not in ("visual_log", "light_curve"):
                raise DomainError(
                    f"produto COBS prefere visual_log ou light_curve "
                    f"(e {product.product_type})"
                )
        fields = fields_from_comet_context(
            self.archive, product, overrides=overrides
        )
        if not fields["designation"]:
            raise DomainError("designation do cometa obrigatoria")
        if not fields["epoch_utc"]:
            raise DomainError("epoch_utc / UT date obrigatoria")
        if fields["mag"] is None:
            raise DomainError("magnitude total obrigatoria")
        text = format_cobs_measure(
            designation=fields["designation"],
            epoch_utc=fields["epoch_utc"],
            mag=float(fields["mag"]),
            mag_method=fields["mag_method"],
            comp_cat=fields["comp_cat"],
            aperture_cm=fields["aperture_cm"],
            instr_type=fields["instr_type"],
            focal_ratio=fields["focal_ratio"],
            power_or_exptime=fields["power_or_exptime"],
            coma_arcmin=fields["coma_arcmin"],
            dc=fields["dc"],
            tail_deg=fields["tail_deg"],
            tail_pa=fields["tail_pa"],
            obscode=fields["obscode"],
            observer=fields["observer"],
            location=fields["location"],
            notes=fields["notes"],
        )
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
        if write_csv:
            csv_path = out_path.with_suffix(".csv")
            csv_path.write_text(
                format_cobs_csv(
                    designation=fields["designation"],
                    epoch_utc=fields["epoch_utc"],
                    mag=float(fields["mag"]),
                    mag_method=fields["mag_method"],
                    comp_cat=fields["comp_cat"],
                    aperture_cm=fields["aperture_cm"],
                    instr_type=fields["instr_type"],
                    focal_ratio=fields["focal_ratio"],
                    power_or_exptime=fields["power_or_exptime"],
                    coma_arcmin=fields["coma_arcmin"],
                    dc=fields["dc"],
                    tail_deg=fields["tail_deg"],
                    tail_pa=fields["tail_pa"],
                    obscode=fields["obscode"],
                    observer=fields["observer"],
                    location=fields["location"],
                ),
                encoding="utf-8",
            )
        return out_path
