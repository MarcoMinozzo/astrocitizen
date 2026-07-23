"""Validacao de produto minimo por rede (AC-141 / RN-080)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass
class ValidationIssue:
    code: str
    message: str
    severity: str = "error"  # error | warning


@dataclass
class ValidationResult:
    ok: bool
    issues: list[ValidationIssue] = field(default_factory=list)

    def error_messages(self) -> list[str]:
        return [i.message for i in self.issues if i.severity == "error"]


def _issue(code: str, message: str, *, severity: str = "error") -> ValidationIssue:
    return ValidationIssue(code=code, message=message, severity=severity)


def validate_product_for_network(
    archive: Any,
    *,
    network: str,
    product_id: UUID | None = None,
    payload: dict[str, Any] | None = None,
) -> ValidationResult:
    """Valida campos minimos atlas antes de export/submit.

    `payload` leva dados do formulario (obscode, star, designation, ...).
    """
    net = (network or "").strip().lower()
    payload = dict(payload or {})
    issues: list[ValidationIssue] = []
    product = None
    points: list[dict] = []
    if product_id is not None:
        product = archive.get_analysis_product(product_id)
        if product is None:
            issues.append(_issue("product_missing", f"produto nao encontrado: {product_id}"))
            return ValidationResult(ok=False, issues=issues)
        points = archive.list_measurement_points(product_id)

    if net == "aavso":
        issues.extend(_validate_aavso(product, points, payload))
    elif net == "mpc":
        issues.extend(_validate_mpc(product, payload))
    elif net == "exoclock":
        issues.extend(_validate_exoclock(product, points, payload))
    elif net == "bess":
        issues.extend(_validate_bess(product, payload))
    elif net == "tns":
        issues.extend(_validate_tns(payload))
    elif net == "iota":
        issues.extend(_validate_iota(payload))
    elif net == "solar":
        issues.extend(_validate_solar(product))
    elif net == "wds":
        issues.extend(_validate_wds(product, payload))
    else:
        issues.append(
            _issue("network_unknown", f"rede sem regras AC-141: {network}", severity="warning")
        )

    errors = [i for i in issues if i.severity == "error"]
    return ValidationResult(ok=len(errors) == 0, issues=issues)


def _validate_aavso(
    product: Any | None, points: list[dict], payload: dict[str, Any]
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if product is None:
        issues.append(_issue("aavso_product", "AAVSO Extended exige product_id"))
        return issues
    if not points:
        issues.append(_issue("aavso_points", "produto sem measurement_points"))
    obscode = str(payload.get("obscode") or "").strip()
    if not obscode:
        issues.append(_issue("aavso_obscode", "OBSCODE AAVSO obrigatorio"))
    star = str(payload.get("star") or payload.get("star_name") or "").strip()
    if not star or star.upper() == "UNKNOWN":
        issues.append(
            _issue("aavso_star", "nome da estrela obrigatorio (nao use UNKNOWN)")
        )
    return issues


def _validate_mpc(product: Any | None, payload: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    code = str(payload.get("observatory_code") or payload.get("obs_code") or "").strip()
    if not code:
        issues.append(_issue("mpc_code", "codigo de observatorio MPC obrigatorio"))
    desig = str(payload.get("designation") or "").strip()
    if not desig:
        issues.append(_issue("mpc_desig", "designacao do objecto obrigatoria"))
    if product is not None and product.product_type == "astrometry":
        summary = product.summary or {}
        if summary.get("ra_deg") is None or summary.get("dec_deg") is None:
            issues.append(_issue("mpc_radec", "produto astrometry sem ra_deg/dec_deg"))
        if not summary.get("epoch_utc"):
            issues.append(_issue("mpc_epoch", "produto astrometry sem epoch_utc"))
    else:
        # form-driven export
        if payload.get("ra_deg") is None or payload.get("dec_deg") is None:
            issues.append(_issue("mpc_radec_form", "RA/Dec deg obrigatorios no formulario"))
        if not str(payload.get("epoch_utc") or "").strip():
            issues.append(_issue("mpc_epoch_form", "epoch UTC obrigatoria"))
    return issues


def _validate_exoclock(
    product: Any | None, points: list[dict], payload: dict[str, Any]
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if product is None:
        issues.append(_issue("exo_product", "ExoClock exige product_id"))
        return issues
    if not points:
        issues.append(_issue("exo_points", "produto sem measurement_points"))
    target = str(payload.get("target") or "").strip()
    if not target or target.upper() == "TARGET":
        issues.append(_issue("exo_target", "target ExoClock obrigatorio"))
    return issues


def _validate_bess(product: Any | None, payload: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if product is not None:
        params = product.parameters or {}
        if product.product_type not in ("spectrum_1d", "spectrum_report") and not params.get(
            "spectrum_uri"
        ):
            issues.append(
                _issue(
                    "bess_type",
                    "BeSS prefere produto spectrum_1d com spectrum_uri",
                    severity="warning",
                )
            )
    obj = str(payload.get("objname") or payload.get("object") or "").strip()
    if "objname" in payload or "object" in payload:
        if not obj:
            issues.append(_issue("bess_objname", "OBJNAME BeSS obrigatorio"))
    observer = str(payload.get("observer") or "").strip()
    if not observer:
        issues.append(_issue("bess_observer", "observer BeSS obrigatorio", severity="warning"))
    return issues


def _validate_tns(payload: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if payload.get("ra_deg") is None or payload.get("dec_deg") is None:
        issues.append(_issue("tns_radec", "TNS AT-rep exige RA/Dec"))
    return issues


def _validate_iota(payload: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for key, label in (
        ("event_id", "Event ID"),
        ("star", "estrela"),
        ("asteroid", "asteroide"),
        ("observer", "observador"),
    ):
        if not str(payload.get(key) or "").strip():
            issues.append(_issue(f"iota_{key}", f"IOTA: {label} obrigatorio"))
    return issues


def _validate_solar(product: Any | None) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if product is None:
        issues.append(_issue("solar_product", "export solar exige product_id"))
        return issues
    if product.product_type != "solar_sunspots":
        issues.append(
            _issue(
                "solar_type",
                f"produto deve ser solar_sunspots (e {product.product_type})",
            )
        )
    return issues


def _validate_wds(
    product: Any | None, payload: dict[str, Any] | None = None
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    payload = dict(payload or {})
    if product is None:
        issues.append(_issue("wds_product", "WDS exige produto double_measure"))
        return issues
    if product.product_type != "double_measure":
        issues.append(_issue("wds_type", "produto deve ser double_measure"))
        return issues
    summary = product.summary or {}
    params = product.parameters or {}
    if summary.get("pa_deg") is None or summary.get("sep_arcsec") is None:
        issues.append(_issue("wds_pasep", "double_measure sem pa_deg/sep_arcsec"))
    if not summary.get("epoch_utc"):
        issues.append(_issue("wds_epoch", "double_measure sem epoch_utc"))
    obj = str(
        payload.get("object")
        or payload.get("object_name")
        or summary.get("object")
        or params.get("object_name")
        or ""
    ).strip()
    if not obj:
        issues.append(_issue("wds_object", "identificacao do par WDS obrigatoria"))
    return issues
