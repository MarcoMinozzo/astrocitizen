"""Painel Contribute: envios AAVSO / MPC / TNS (AC-143 / R2 Revisar campos)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID


def submission_table_rows(subs: list[Any]) -> list[list[str]]:
    rows: list[list[str]] = []
    for s in subs:
        rows.append(
            [
                str(getattr(s, "created_at", "") or ""),
                str(getattr(s, "network", "") or ""),
                str(getattr(s, "status", "") or ""),
                str(getattr(s, "id", ""))[:8],
                (getattr(s, "artifact_uri", None) or "-")[:72],
            ]
        )
    return rows


def credentials_status_lines(store: Any) -> list[str]:
    data = store.load()
    lines = []
    for net in ("aavso", "mpc", "tns", "bess", "exoclock", "iota", "wds", "cobs"):
        vals = dict(data.get(net) or {})
        if not vals:
            lines.append(f"{net}: (sem credenciais)")
            continue
        keys = []
        if net == "aavso" and vals.get("obscode"):
            keys.append(f"obscode={vals['obscode']}")
        if net == "mpc":
            if vals.get("observatory_code"):
                keys.append(f"code={vals['observatory_code']}")
            if vals.get("email"):
                keys.append("email=set")
        if net == "tns":
            if vals.get("api_key"):
                keys.append("api_key=***")
            if vals.get("user_id"):
                keys.append(f"user_id={vals['user_id']}")
            if vals.get("groupid") is not None:
                keys.append(f"groupid={vals['groupid']}")
        if net == "cobs" and vals.get("obscode"):
            keys.append(f"obscode={vals['obscode']}")
        if net in ("bess", "exoclock", "iota", "wds", "cobs") and vals.get("observer"):
            keys.append(f"observer={vals['observer']}")
        lines.append(f"{net}: {', '.join(keys) if keys else '(vazio)'}")
    return lines


def _parse_uuid(raw: Any) -> UUID | None:
    text = str(raw or "").strip()
    if not text:
        return None
    try:
        return UUID(text)
    except ValueError:
        return None


def _star_from_product(archive: Any, product: Any) -> str | None:
    params = dict(getattr(product, "parameters", None) or {})
    summary = dict(getattr(product, "summary", None) or {})
    for key in ("auid", "star", "star_name", "target_name", "target", "object"):
        val = params.get(key) or summary.get(key)
        if val and str(val).strip().upper() not in ("", "UNKNOWN", "TARGET"):
            return str(val).strip()
    tid = params.get("target_id") or summary.get("target_id")
    uid = _parse_uuid(tid)
    if uid is not None and hasattr(archive, "get_target"):
        target = archive.get_target(uid)
        if target is not None:
            ids = dict(getattr(target, "external_ids", None) or {})
            for key in ("auid", "vsx"):
                val = ids.get(key)
                if val and str(val).strip():
                    return str(val).strip()
            desig = getattr(target, "designation", None)
            if desig:
                return str(desig).strip()
    return None


def prefill_aavso_fields(
    archive: Any,
    *,
    credentials: dict[str, Any] | None = None,
    current: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Preenche rascunho AAVSO a partir de credenciais + produto (atlas / AC-141)."""
    cred = dict(credentials or {})
    cur = dict(current or {})
    out: dict[str, Any] = {
        "product_id": str(cur.get("product_id") or "").strip(),
        "star": str(cur.get("star") or "").strip(),
        "obscode": str(cur.get("obscode") or cred.get("obscode") or "").strip(),
        "band": str(cur.get("band") or "V").strip() or "V",
        "chart": str(cur.get("chart") or "NA").strip() or "NA",
    }
    pid = _parse_uuid(out["product_id"])
    if pid is None:
        return out
    product = archive.get_analysis_product(pid)
    if product is None:
        return out
    params = dict(product.parameters or {})
    if not out["star"] or out["star"].upper() == "UNKNOWN":
        star = _star_from_product(archive, product)
        if star:
            out["star"] = star
    if (not cur.get("band") or str(cur.get("band")) == "V") and params.get("band"):
        out["band"] = str(params["band"]).strip() or out["band"]
    if (not cur.get("chart") or str(cur.get("chart")) == "NA") and params.get("chart"):
        out["chart"] = str(params["chart"]).strip() or out["chart"]
    return out


def prefill_mpc_fields(
    archive: Any,
    *,
    credentials: dict[str, Any] | None = None,
    current: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Preenche rascunho MPC (espelha CLI contribute mpc --product)."""
    cred = dict(credentials or {})
    cur = dict(current or {})
    out: dict[str, Any] = {
        "product_id": str(cur.get("product_id") or "").strip(),
        "designation": str(cur.get("designation") or "").strip(),
        "observatory_code": str(
            cur.get("observatory_code") or cur.get("obs_code") or cred.get("observatory_code") or ""
        ).strip(),
        "epoch_utc": str(cur.get("epoch_utc") or "").strip(),
        "ra_deg": cur.get("ra_deg"),
        "dec_deg": cur.get("dec_deg"),
        "mag": cur.get("mag"),
        "band": str(cur.get("band") or "").strip(),
        "email": str(cur.get("email") or cred.get("email") or "").strip(),
    }
    pid = _parse_uuid(out["product_id"])
    if pid is None:
        return out
    product = archive.get_analysis_product(pid)
    if product is None:
        return out
    params = dict(product.parameters or {})
    summary = dict(product.summary or {})
    if not out["designation"]:
        out["designation"] = str(
            params.get("designation") or summary.get("designation") or ""
        ).strip()
    if not out["epoch_utc"]:
        out["epoch_utc"] = str(summary.get("epoch_utc") or "").strip()
    if out["ra_deg"] is None and summary.get("ra_deg") is not None:
        out["ra_deg"] = float(summary["ra_deg"])
    if out["dec_deg"] is None and summary.get("dec_deg") is not None:
        out["dec_deg"] = float(summary["dec_deg"])
    if out["mag"] is None and summary.get("mag") is not None:
        out["mag"] = float(summary["mag"])
    if not out["band"]:
        out["band"] = str(params.get("band") or summary.get("band") or "R").strip() or "R"
    return out


def prefill_wds_fields(
    archive: Any,
    *,
    credentials: dict[str, Any] | None = None,
    current: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Preenche rascunho WDS a partir de produto double_measure."""
    from astrocitizen.contribution.wds import fields_from_double_product

    cred = dict(credentials or {})
    cur = dict(current or {})
    out: dict[str, Any] = {
        "product_id": str(cur.get("product_id") or "").strip(),
        "object": str(cur.get("object") or cur.get("object_name") or "").strip(),
        "epoch_utc": str(cur.get("epoch_utc") or "").strip(),
        "pa_deg": cur.get("pa_deg"),
        "sep_arcsec": cur.get("sep_arcsec"),
        "method": str(cur.get("method") or "").strip(),
        "mag_primary": cur.get("mag_primary"),
        "mag_secondary": cur.get("mag_secondary"),
        "observer": str(cur.get("observer") or cred.get("observer") or "").strip(),
        "observatory": str(cur.get("observatory") or "").strip(),
        "discoverer": str(cur.get("discoverer") or "").strip(),
        "notes": str(cur.get("notes") or "").strip(),
    }
    pid = _parse_uuid(out["product_id"])
    if pid is None:
        if not out["method"]:
            out["method"] = "micrometer"
        return out
    product = archive.get_analysis_product(pid)
    if product is None:
        if not out["method"]:
            out["method"] = "micrometer"
        return out
    # Product wins for measure fields; form only supplies missing identity/meta.
    filled = fields_from_double_product(archive, product)
    out["object"] = filled["object_name"] or out["object"]
    out["epoch_utc"] = filled["epoch_utc"] or out["epoch_utc"]
    out["pa_deg"] = filled["pa_deg"]
    out["sep_arcsec"] = filled["sep_arcsec"]
    out["method"] = filled["method"] or out["method"] or "micrometer"
    out["mag_primary"] = filled["mag_primary"]
    out["mag_secondary"] = filled["mag_secondary"]
    out["observer"] = filled["observer"] or out["observer"] or "AstroCitizen"
    out["observatory"] = filled["observatory"] or out["observatory"]
    out["discoverer"] = filled["discoverer"] or out["discoverer"]
    out["notes"] = filled["notes"] or out["notes"]
    return out


def prefill_tns_fields(
    archive: Any,
    *,
    credentials: dict[str, Any] | None = None,
    current: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Preenche rascunho TNS (form ou produto blink/astrometry)."""
    cred = dict(credentials or {})
    cur = dict(current or {})
    out: dict[str, Any] = {
        "product_id": str(cur.get("product_id") or "").strip(),
        "ra_deg": cur.get("ra_deg"),
        "dec_deg": cur.get("dec_deg"),
        "mag": cur.get("mag"),
        "groupid": str(cur.get("groupid") if cur.get("groupid") is not None else ""),
    }
    if out["groupid"] == "" and cred.get("groupid") is not None:
        out["groupid"] = str(cred["groupid"])
    pid = _parse_uuid(out["product_id"])
    if pid is None:
        return out
    product = archive.get_analysis_product(pid)
    if product is None:
        return out
    summary = dict(product.summary or {})
    params = dict(product.parameters or {})
    if out["ra_deg"] is None and summary.get("ra_deg") is not None:
        out["ra_deg"] = float(summary["ra_deg"])
    if out["dec_deg"] is None and summary.get("dec_deg") is not None:
        out["dec_deg"] = float(summary["dec_deg"])
    if out["mag"] is None:
        for key in ("mag", "discovery_mag", "mag_approx"):
            if summary.get(key) is not None:
                out["mag"] = float(summary[key])
                break
            if params.get(key) is not None:
                out["mag"] = float(params[key])
                break
    return out


def prefill_exoclock_fields(
    archive: Any,
    *,
    credentials: dict[str, Any] | None = None,
    current: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Preenche rascunho ExoClock a partir do produto LC."""
    cred = dict(credentials or {})
    cur = dict(current or {})
    out: dict[str, Any] = {
        "product_id": str(cur.get("product_id") or "").strip(),
        "target": str(cur.get("target") or "").strip(),
        "observer": str(cur.get("observer") or cred.get("observer") or "").strip(),
    }
    pid = _parse_uuid(out["product_id"])
    if pid is None:
        return out
    product = archive.get_analysis_product(pid)
    if product is None:
        return out
    params = dict(product.parameters or {})
    summary = dict(product.summary or {})
    if not out["target"] or out["target"].upper() == "TARGET":
        for key in ("target", "target_name", "object", "planet"):
            val = params.get(key) or summary.get(key)
            if val and str(val).strip().upper() not in ("", "TARGET"):
                out["target"] = str(val).strip()
                break
        if (not out["target"] or out["target"].upper() == "TARGET") and params.get(
            "target_id"
        ):
            tid = _parse_uuid(params.get("target_id"))
            if tid is not None and hasattr(archive, "get_target"):
                tgt = archive.get_target(tid)
                if tgt is not None and getattr(tgt, "designation", None):
                    out["target"] = str(tgt.designation).strip()
    return out


def prefill_bess_fields(
    archive: Any,
    *,
    credentials: dict[str, Any] | None = None,
    current: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Preenche rascunho BeSS (form ou spectrum_1d)."""
    cred = dict(credentials or {})
    cur = dict(current or {})
    out: dict[str, Any] = {
        "product_id": str(cur.get("product_id") or "").strip(),
        "objname": str(cur.get("objname") or cur.get("object") or "").strip(),
        "observer": str(cur.get("observer") or cred.get("observer") or "").strip(),
        "date_obs": str(cur.get("date_obs") or "").strip(),
    }
    pid = _parse_uuid(out["product_id"])
    if pid is None:
        return out
    product = archive.get_analysis_product(pid)
    if product is None:
        return out
    params = dict(product.parameters or {})
    summary = dict(product.summary or {})
    if not out["objname"]:
        for key in ("objname", "object", "target_name", "star"):
            val = params.get(key) or summary.get(key)
            if val:
                out["objname"] = str(val).strip()
                break
    if not out["date_obs"]:
        out["date_obs"] = str(
            params.get("date_obs") or summary.get("epoch_utc") or summary.get("date_obs") or ""
        ).strip()
    if not out["observer"]:
        out["observer"] = str(
            params.get("observer") or summary.get("observer") or cred.get("observer") or ""
        ).strip()
    return out


def prefill_iota_fields(
    archive: Any,
    *,
    credentials: dict[str, Any] | None = None,
    current: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Preenche rascunho IOTA a partir de occultation_* ou form."""
    cred = dict(credentials or {})
    cur = dict(current or {})
    out: dict[str, Any] = {
        "product_id": str(cur.get("product_id") or "").strip(),
        "event_id": str(cur.get("event_id") or "").strip(),
        "star": str(cur.get("star") or "").strip(),
        "asteroid": str(cur.get("asteroid") or "").strip(),
        "observer": str(cur.get("observer") or cred.get("observer") or "").strip(),
        "result": str(cur.get("result") or "positive").strip() or "positive",
    }
    pid = _parse_uuid(out["product_id"])
    if pid is None:
        return out
    product = archive.get_analysis_product(pid)
    if product is None:
        return out
    params = dict(product.parameters or {})
    summary = dict(product.summary or {})
    if not out["event_id"]:
        out["event_id"] = str(
            params.get("event_id") or summary.get("event_id") or ""
        ).strip()
    if not out["star"]:
        out["star"] = str(params.get("star") or summary.get("star") or "").strip()
    if not out["asteroid"]:
        out["asteroid"] = str(
            params.get("asteroid") or summary.get("asteroid") or ""
        ).strip()
    if not out["observer"]:
        out["observer"] = str(
            params.get("observer") or summary.get("observer") or cred.get("observer") or ""
        ).strip()
    if cur.get("result") is None and (params.get("result") or summary.get("result")):
        out["result"] = str(params.get("result") or summary.get("result")).strip()
    return out


def prefill_cobs_fields(
    archive: Any,
    *,
    credentials: dict[str, Any] | None = None,
    current: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Preenche rascunho COBS a partir de visual_log / light_curve."""
    from astrocitizen.contribution.cobs import fields_from_comet_context

    cred = dict(credentials or {})
    cur = dict(current or {})
    out: dict[str, Any] = {
        "product_id": str(cur.get("product_id") or "").strip(),
        "designation": str(cur.get("designation") or "").strip(),
        "epoch_utc": str(cur.get("epoch_utc") or "").strip(),
        "mag": cur.get("mag"),
        "mag_method": str(cur.get("mag_method") or "B").strip() or "B",
        "comp_cat": str(cur.get("comp_cat") or "").strip(),
        "aperture_cm": cur.get("aperture_cm"),
        "instr_type": str(cur.get("instr_type") or "L").strip() or "L",
        "coma_arcmin": cur.get("coma_arcmin"),
        "dc": str(cur.get("dc") or "").strip(),
        "tail_deg": cur.get("tail_deg"),
        "tail_pa": cur.get("tail_pa"),
        "obscode": str(cur.get("obscode") or cred.get("obscode") or "").strip(),
        "observer": str(cur.get("observer") or cred.get("observer") or "").strip(),
        "location": str(cur.get("location") or "").strip(),
        "notes": str(cur.get("notes") or "").strip(),
    }
    pid = _parse_uuid(out["product_id"])
    product = archive.get_analysis_product(pid) if pid else None
    filled = fields_from_comet_context(
        archive,
        product,
        overrides={
            "designation": out["designation"] or None,
            "epoch_utc": out["epoch_utc"] or None,
            "mag": out["mag"],
            "mag_method": out["mag_method"] if cur.get("mag_method") else None,
            "comp_cat": out["comp_cat"] or None,
            "aperture_cm": out["aperture_cm"],
            "instr_type": out["instr_type"] if cur.get("instr_type") else None,
            "coma_arcmin": out["coma_arcmin"],
            "dc": out["dc"] or None,
            "tail_deg": out["tail_deg"],
            "tail_pa": out["tail_pa"],
            "obscode": out["obscode"] or None,
            "observer": out["observer"] or None,
            "location": out["location"] or None,
            "notes": out["notes"] or None,
        },
    )
    # Product/context wins for empty designation/epoch/mag
    out["designation"] = filled["designation"] or out["designation"]
    out["epoch_utc"] = filled["epoch_utc"] or out["epoch_utc"]
    if out["mag"] is None:
        out["mag"] = filled["mag"]
    out["mag_method"] = filled["mag_method"] or out["mag_method"]
    out["comp_cat"] = filled["comp_cat"] or out["comp_cat"]
    if out["aperture_cm"] is None:
        out["aperture_cm"] = filled["aperture_cm"]
    out["instr_type"] = filled["instr_type"] or out["instr_type"]
    if out["coma_arcmin"] is None:
        out["coma_arcmin"] = filled["coma_arcmin"]
    out["dc"] = filled["dc"] or out["dc"]
    if out["tail_deg"] is None:
        out["tail_deg"] = filled["tail_deg"]
    if out["tail_pa"] is None:
        out["tail_pa"] = filled["tail_pa"]
    out["obscode"] = filled["obscode"] or out["obscode"]
    out["observer"] = filled["observer"] or out["observer"] or "AstroCitizen"
    out["location"] = filled["location"] or out["location"]
    out["notes"] = filled["notes"] or out["notes"]
    return out


def format_validation_issue_lines(result: Any) -> list[str]:
    lines: list[str] = []
    for issue in getattr(result, "issues", None) or []:
        sev = getattr(issue, "severity", "error")
        code = getattr(issue, "code", "")
        msg = getattr(issue, "message", "")
        lines.append(f"[{sev}] {code}: {msg}")
    return lines


def build_contribute_dashboard(parent: Any | None = None) -> Any:
    """Devolve ContributeDashboard (requer PySide6)."""
    from PySide6.QtWidgets import (
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QDoubleSpinBox,
        QFormLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QMessageBox,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QTabWidget,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    from astrocitizen.adapters.fs import LocalArtifactStore
    from astrocitizen.contribution.aavso import ExportAavso
    from astrocitizen.contribution.bess import write_bess_fits
    from astrocitizen.contribution.credentials import LocalCredentialsStore
    from astrocitizen.contribution.exoclock import ExportExoclock
    from astrocitizen.contribution.iota import write_iota_pack
    from astrocitizen.contribution.models import NetworkSubmission
    from astrocitizen.contribution.mpc import MpcAdesSubmitter, write_ades_psv
    from astrocitizen.contribution.tns import (
        TnsClient,
        format_tns_at_report,
        write_tns_report,
    )
    from astrocitizen.contribution.validate_minimum import validate_product_for_network
    from astrocitizen.contribution.wds import ExportWds
    from astrocitizen.contribution.cobs import ExportCobs
    from astrocitizen.shared.ids import new_id
    from astrocitizen.shared.paths import default_artifacts_root

    class FieldReviewDialog(QDialog):
        """Revisar campos atlas antes de export (AAVSO/MPC/WDS + R3)."""

        def __init__(
            self,
            parent: QWidget | None,
            *,
            network: str,
            archive: Any,
            initial: dict[str, Any],
        ) -> None:
            super().__init__(parent)
            self.network = network.lower()
            self.archive = archive
            self.setWindowTitle(
                f"Revisar campos — {self.network.upper()} (atlas)"
            )
            self.resize(480, 460)
            lay = QVBoxLayout(self)
            form = QFormLayout()
            self._fields: dict[str, Any] = {}
            if self.network == "aavso":
                self._fields["product_id"] = QLineEdit(str(initial.get("product_id") or ""))
                self._fields["star"] = QLineEdit(str(initial.get("star") or ""))
                self._fields["obscode"] = QLineEdit(str(initial.get("obscode") or ""))
                self._fields["band"] = QLineEdit(str(initial.get("band") or "V"))
                self._fields["chart"] = QLineEdit(str(initial.get("chart") or "NA"))
                form.addRow("Product UUID", self._fields["product_id"])
                form.addRow("Star / STARID", self._fields["star"])
                form.addRow("OBSCODE", self._fields["obscode"])
                form.addRow("Band", self._fields["band"])
                form.addRow("Chart", self._fields["chart"])
            elif self.network == "wds":
                self._fields["product_id"] = QLineEdit(str(initial.get("product_id") or ""))
                self._fields["object"] = QLineEdit(str(initial.get("object") or ""))
                self._fields["epoch_utc"] = QLineEdit(str(initial.get("epoch_utc") or ""))
                self._fields["pa_deg"] = QDoubleSpinBox()
                self._fields["pa_deg"].setRange(0, 359.999)
                self._fields["pa_deg"].setDecimals(3)
                if initial.get("pa_deg") is not None:
                    self._fields["pa_deg"].setValue(float(initial["pa_deg"]))
                self._fields["sep_arcsec"] = QDoubleSpinBox()
                self._fields["sep_arcsec"].setRange(0.001, 9999)
                self._fields["sep_arcsec"].setDecimals(3)
                if initial.get("sep_arcsec") is not None:
                    self._fields["sep_arcsec"].setValue(float(initial["sep_arcsec"]))
                self._fields["mag_primary"] = QDoubleSpinBox()
                self._fields["mag_primary"].setRange(-1, 30)
                self._fields["mag_primary"].setDecimals(2)
                self._fields["mag_primary"].setSpecialValueText("(vazio)")
                self._fields["mag_primary"].setValue(
                    float(initial["mag_primary"])
                    if initial.get("mag_primary") is not None
                    else -1
                )
                self._fields["mag_secondary"] = QDoubleSpinBox()
                self._fields["mag_secondary"].setRange(-1, 30)
                self._fields["mag_secondary"].setDecimals(2)
                self._fields["mag_secondary"].setSpecialValueText("(vazio)")
                self._fields["mag_secondary"].setValue(
                    float(initial["mag_secondary"])
                    if initial.get("mag_secondary") is not None
                    else -1
                )
                self._fields["method"] = QComboBox()
                for m in ("micrometer", "imaging_manual", "other"):
                    self._fields["method"].addItem(m, m)
                meth = str(initial.get("method") or "micrometer")
                mi = self._fields["method"].findData(meth)
                if mi >= 0:
                    self._fields["method"].setCurrentIndex(mi)
                self._fields["observer"] = QLineEdit(str(initial.get("observer") or ""))
                self._fields["observatory"] = QLineEdit(
                    str(initial.get("observatory") or "")
                )
                self._fields["discoverer"] = QLineEdit(
                    str(initial.get("discoverer") or "")
                )
                self._fields["notes"] = QLineEdit(str(initial.get("notes") or ""))
                form.addRow("Product UUID", self._fields["product_id"])
                form.addRow("WDS / object", self._fields["object"])
                form.addRow("Epoch UTC", self._fields["epoch_utc"])
                form.addRow("PA deg", self._fields["pa_deg"])
                form.addRow("Sep arcsec", self._fields["sep_arcsec"])
                form.addRow("Mag1", self._fields["mag_primary"])
                form.addRow("Mag2", self._fields["mag_secondary"])
                form.addRow("Method", self._fields["method"])
                form.addRow("Observer", self._fields["observer"])
                form.addRow("Observatory", self._fields["observatory"])
                form.addRow("Discoverer", self._fields["discoverer"])
                form.addRow("Notes", self._fields["notes"])
            elif self.network == "tns":
                self._fields["product_id"] = QLineEdit(str(initial.get("product_id") or ""))
                self._fields["ra_deg"] = QDoubleSpinBox()
                self._fields["ra_deg"].setRange(0, 360)
                self._fields["ra_deg"].setDecimals(6)
                if initial.get("ra_deg") is not None:
                    self._fields["ra_deg"].setValue(float(initial["ra_deg"]))
                self._fields["dec_deg"] = QDoubleSpinBox()
                self._fields["dec_deg"].setRange(-90, 90)
                self._fields["dec_deg"].setDecimals(6)
                if initial.get("dec_deg") is not None:
                    self._fields["dec_deg"].setValue(float(initial["dec_deg"]))
                self._fields["mag"] = QDoubleSpinBox()
                self._fields["mag"].setRange(0, 30)
                self._fields["mag"].setDecimals(3)
                self._fields["mag"].setValue(
                    float(initial["mag"]) if initial.get("mag") is not None else 19.0
                )
                self._fields["groupid"] = QLineEdit(str(initial.get("groupid") or "0"))
                form.addRow("Product UUID", self._fields["product_id"])
                form.addRow("RA deg", self._fields["ra_deg"])
                form.addRow("Dec deg", self._fields["dec_deg"])
                form.addRow("Mag", self._fields["mag"])
                form.addRow("Group id", self._fields["groupid"])
            elif self.network == "exoclock":
                self._fields["product_id"] = QLineEdit(str(initial.get("product_id") or ""))
                self._fields["target"] = QLineEdit(str(initial.get("target") or ""))
                self._fields["observer"] = QLineEdit(str(initial.get("observer") or ""))
                form.addRow("Product UUID", self._fields["product_id"])
                form.addRow("Target", self._fields["target"])
                form.addRow("Observer", self._fields["observer"])
            elif self.network == "bess":
                self._fields["product_id"] = QLineEdit(str(initial.get("product_id") or ""))
                self._fields["objname"] = QLineEdit(str(initial.get("objname") or ""))
                self._fields["observer"] = QLineEdit(str(initial.get("observer") or ""))
                self._fields["date_obs"] = QLineEdit(str(initial.get("date_obs") or ""))
                form.addRow("Product UUID", self._fields["product_id"])
                form.addRow("OBJNAME", self._fields["objname"])
                form.addRow("Observer", self._fields["observer"])
                form.addRow("DATE-OBS", self._fields["date_obs"])
            elif self.network == "iota":
                self._fields["product_id"] = QLineEdit(str(initial.get("product_id") or ""))
                self._fields["event_id"] = QLineEdit(str(initial.get("event_id") or ""))
                self._fields["star"] = QLineEdit(str(initial.get("star") or ""))
                self._fields["asteroid"] = QLineEdit(str(initial.get("asteroid") or ""))
                self._fields["observer"] = QLineEdit(str(initial.get("observer") or ""))
                self._fields["result"] = QComboBox()
                self._fields["result"].addItems(["positive", "negative"])
                res = str(initial.get("result") or "positive")
                ri = self._fields["result"].findText(res)
                if ri >= 0:
                    self._fields["result"].setCurrentIndex(ri)
                form.addRow("Product UUID", self._fields["product_id"])
                form.addRow("Event ID", self._fields["event_id"])
                form.addRow("Star", self._fields["star"])
                form.addRow("Asteroid", self._fields["asteroid"])
                form.addRow("Observer", self._fields["observer"])
                form.addRow("Result", self._fields["result"])
            elif self.network == "cobs":
                self._fields["product_id"] = QLineEdit(str(initial.get("product_id") or ""))
                self._fields["designation"] = QLineEdit(
                    str(initial.get("designation") or "")
                )
                self._fields["epoch_utc"] = QLineEdit(str(initial.get("epoch_utc") or ""))
                self._fields["mag"] = QDoubleSpinBox()
                self._fields["mag"].setRange(-5, 25)
                self._fields["mag"].setDecimals(1)
                self._fields["mag"].setSpecialValueText("(vazio)")
                self._fields["mag"].setMinimum(-5.1)
                self._fields["mag"].setValue(
                    float(initial["mag"]) if initial.get("mag") is not None else -5.1
                )
                self._fields["mag_method"] = QLineEdit(
                    str(initial.get("mag_method") or "B")
                )
                self._fields["comp_cat"] = QLineEdit(str(initial.get("comp_cat") or ""))
                self._fields["aperture_cm"] = QDoubleSpinBox()
                self._fields["aperture_cm"].setRange(0, 999)
                self._fields["aperture_cm"].setDecimals(1)
                self._fields["aperture_cm"].setSpecialValueText("(vazio)")
                self._fields["aperture_cm"].setValue(
                    float(initial["aperture_cm"])
                    if initial.get("aperture_cm") is not None
                    else 0
                )
                self._fields["instr_type"] = QLineEdit(
                    str(initial.get("instr_type") or "L")
                )
                self._fields["coma_arcmin"] = QDoubleSpinBox()
                self._fields["coma_arcmin"].setRange(0, 999)
                self._fields["coma_arcmin"].setDecimals(1)
                self._fields["coma_arcmin"].setSpecialValueText("(vazio)")
                self._fields["coma_arcmin"].setValue(
                    float(initial["coma_arcmin"])
                    if initial.get("coma_arcmin") is not None
                    else 0
                )
                self._fields["dc"] = QLineEdit(str(initial.get("dc") or ""))
                self._fields["obscode"] = QLineEdit(str(initial.get("obscode") or ""))
                self._fields["observer"] = QLineEdit(str(initial.get("observer") or ""))
                self._fields["location"] = QLineEdit(str(initial.get("location") or ""))
                self._fields["notes"] = QLineEdit(str(initial.get("notes") or ""))
                form.addRow("Product UUID", self._fields["product_id"])
                form.addRow("Designation", self._fields["designation"])
                form.addRow("Epoch UTC", self._fields["epoch_utc"])
                form.addRow("Mag", self._fields["mag"])
                form.addRow("Mag method", self._fields["mag_method"])
                form.addRow("Comp cat", self._fields["comp_cat"])
                form.addRow("Aperture cm", self._fields["aperture_cm"])
                form.addRow("Instr type", self._fields["instr_type"])
                form.addRow("Coma '", self._fields["coma_arcmin"])
                form.addRow("DC", self._fields["dc"])
                form.addRow("OBSCODE", self._fields["obscode"])
                form.addRow("Observer", self._fields["observer"])
                form.addRow("Location", self._fields["location"])
                form.addRow("Notes", self._fields["notes"])
            else:
                self._fields["product_id"] = QLineEdit(str(initial.get("product_id") or ""))
                self._fields["designation"] = QLineEdit(
                    str(initial.get("designation") or "")
                )
                self._fields["observatory_code"] = QLineEdit(
                    str(initial.get("observatory_code") or "")
                )
                self._fields["epoch_utc"] = QLineEdit(str(initial.get("epoch_utc") or ""))
                self._fields["ra_deg"] = QDoubleSpinBox()
                self._fields["ra_deg"].setRange(0, 360)
                self._fields["ra_deg"].setDecimals(6)
                if initial.get("ra_deg") is not None:
                    self._fields["ra_deg"].setValue(float(initial["ra_deg"]))
                self._fields["dec_deg"] = QDoubleSpinBox()
                self._fields["dec_deg"].setRange(-90, 90)
                self._fields["dec_deg"].setDecimals(6)
                if initial.get("dec_deg") is not None:
                    self._fields["dec_deg"].setValue(float(initial["dec_deg"]))
                self._fields["mag"] = QDoubleSpinBox()
                self._fields["mag"].setRange(0, 30)
                self._fields["mag"].setDecimals(3)
                self._fields["mag"].setSpecialValueText("(vazio)")
                self._fields["mag"].setMinimum(-1)
                self._fields["mag"].setValue(
                    float(initial["mag"]) if initial.get("mag") is not None else -1
                )
                self._fields["band"] = QLineEdit(str(initial.get("band") or "R"))
                self._fields["email"] = QLineEdit(str(initial.get("email") or ""))
                form.addRow("Product UUID", self._fields["product_id"])
                form.addRow("Designation", self._fields["designation"])
                form.addRow("Obs code", self._fields["observatory_code"])
                form.addRow("Epoch UTC", self._fields["epoch_utc"])
                form.addRow("RA deg", self._fields["ra_deg"])
                form.addRow("Dec deg", self._fields["dec_deg"])
                form.addRow("Mag", self._fields["mag"])
                form.addRow("Band", self._fields["band"])
                form.addRow("Email", self._fields["email"])
            lay.addLayout(form)
            btn_row = QHBoxLayout()
            self.btn_prefill = QPushButton("Preencher do produto")
            self.btn_check = QPushButton("Verificar (AC-141)")
            self.btn_prefill.clicked.connect(self._prefill_from_product)
            self.btn_check.clicked.connect(self._run_check)
            btn_row.addWidget(self.btn_prefill)
            btn_row.addWidget(self.btn_check)
            btn_row.addStretch(1)
            lay.addLayout(btn_row)
            self.issues = QListWidget()
            self.status = QLabel("Reveja os campos do atlas e verifique antes de aceitar.")
            self.status.setWordWrap(True)
            lay.addWidget(QLabel("Validacao"))
            lay.addWidget(self.issues, 1)
            lay.addWidget(self.status)
            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )
            buttons.accepted.connect(self._on_accept)
            buttons.rejected.connect(self.reject)
            lay.addWidget(buttons)
            self._run_check()

        def values(self) -> dict[str, Any]:
            if self.network == "aavso":
                return {
                    "product_id": self._fields["product_id"].text().strip(),
                    "star": self._fields["star"].text().strip(),
                    "obscode": self._fields["obscode"].text().strip(),
                    "band": self._fields["band"].text().strip() or "V",
                    "chart": self._fields["chart"].text().strip() or "NA",
                }
            if self.network == "wds":
                m1 = float(self._fields["mag_primary"].value())
                m2 = float(self._fields["mag_secondary"].value())
                return {
                    "product_id": self._fields["product_id"].text().strip(),
                    "object": self._fields["object"].text().strip(),
                    "epoch_utc": self._fields["epoch_utc"].text().strip(),
                    "pa_deg": float(self._fields["pa_deg"].value()),
                    "sep_arcsec": float(self._fields["sep_arcsec"].value()),
                    "mag_primary": None if m1 < 0 else m1,
                    "mag_secondary": None if m2 < 0 else m2,
                    "method": str(
                        self._fields["method"].currentData()
                        or self._fields["method"].currentText()
                    ),
                    "observer": self._fields["observer"].text().strip(),
                    "observatory": self._fields["observatory"].text().strip(),
                    "discoverer": self._fields["discoverer"].text().strip(),
                    "notes": self._fields["notes"].text().strip(),
                }
            if self.network == "tns":
                return {
                    "product_id": self._fields["product_id"].text().strip(),
                    "ra_deg": float(self._fields["ra_deg"].value()),
                    "dec_deg": float(self._fields["dec_deg"].value()),
                    "mag": float(self._fields["mag"].value()),
                    "groupid": self._fields["groupid"].text().strip() or "0",
                }
            if self.network == "exoclock":
                return {
                    "product_id": self._fields["product_id"].text().strip(),
                    "target": self._fields["target"].text().strip(),
                    "observer": self._fields["observer"].text().strip(),
                }
            if self.network == "bess":
                return {
                    "product_id": self._fields["product_id"].text().strip(),
                    "objname": self._fields["objname"].text().strip(),
                    "observer": self._fields["observer"].text().strip(),
                    "date_obs": self._fields["date_obs"].text().strip(),
                }
            if self.network == "iota":
                return {
                    "product_id": self._fields["product_id"].text().strip(),
                    "event_id": self._fields["event_id"].text().strip(),
                    "star": self._fields["star"].text().strip(),
                    "asteroid": self._fields["asteroid"].text().strip(),
                    "observer": self._fields["observer"].text().strip(),
                    "result": self._fields["result"].currentText(),
                }
            if self.network == "cobs":
                mag_val = float(self._fields["mag"].value())
                ap = float(self._fields["aperture_cm"].value())
                coma = float(self._fields["coma_arcmin"].value())
                return {
                    "product_id": self._fields["product_id"].text().strip(),
                    "designation": self._fields["designation"].text().strip(),
                    "epoch_utc": self._fields["epoch_utc"].text().strip(),
                    "mag": None if mag_val < -5 else mag_val,
                    "mag_method": self._fields["mag_method"].text().strip() or "B",
                    "comp_cat": self._fields["comp_cat"].text().strip(),
                    "aperture_cm": None if ap <= 0 else ap,
                    "instr_type": self._fields["instr_type"].text().strip() or "L",
                    "coma_arcmin": None if coma <= 0 else coma,
                    "dc": self._fields["dc"].text().strip(),
                    "obscode": self._fields["obscode"].text().strip(),
                    "observer": self._fields["observer"].text().strip(),
                    "location": self._fields["location"].text().strip(),
                    "notes": self._fields["notes"].text().strip(),
                }
            mag_val = float(self._fields["mag"].value())
            return {
                "product_id": self._fields["product_id"].text().strip(),
                "designation": self._fields["designation"].text().strip(),
                "observatory_code": self._fields["observatory_code"].text().strip(),
                "epoch_utc": self._fields["epoch_utc"].text().strip(),
                "ra_deg": float(self._fields["ra_deg"].value()),
                "dec_deg": float(self._fields["dec_deg"].value()),
                "mag": None if mag_val < 0 else mag_val,
                "band": self._fields["band"].text().strip() or "R",
                "email": self._fields["email"].text().strip(),
            }

        def _apply_filled(self, filled: dict[str, Any]) -> None:
            if self.network == "aavso":
                self._fields["star"].setText(str(filled.get("star") or ""))
                self._fields["band"].setText(str(filled.get("band") or "V"))
                self._fields["chart"].setText(str(filled.get("chart") or "NA"))
            elif self.network == "wds":
                self._fields["object"].setText(str(filled.get("object") or ""))
                self._fields["epoch_utc"].setText(str(filled.get("epoch_utc") or ""))
                if filled.get("pa_deg") is not None:
                    self._fields["pa_deg"].setValue(float(filled["pa_deg"]))
                if filled.get("sep_arcsec") is not None:
                    self._fields["sep_arcsec"].setValue(float(filled["sep_arcsec"]))
                if filled.get("mag_primary") is not None:
                    self._fields["mag_primary"].setValue(float(filled["mag_primary"]))
                if filled.get("mag_secondary") is not None:
                    self._fields["mag_secondary"].setValue(float(filled["mag_secondary"]))
                meth = str(filled.get("method") or "micrometer")
                mi = self._fields["method"].findData(meth)
                if mi >= 0:
                    self._fields["method"].setCurrentIndex(mi)
                self._fields["observer"].setText(str(filled.get("observer") or ""))
                self._fields["observatory"].setText(str(filled.get("observatory") or ""))
                self._fields["discoverer"].setText(str(filled.get("discoverer") or ""))
                self._fields["notes"].setText(str(filled.get("notes") or ""))
            elif self.network == "tns":
                if filled.get("ra_deg") is not None:
                    self._fields["ra_deg"].setValue(float(filled["ra_deg"]))
                if filled.get("dec_deg") is not None:
                    self._fields["dec_deg"].setValue(float(filled["dec_deg"]))
                if filled.get("mag") is not None:
                    self._fields["mag"].setValue(float(filled["mag"]))
                if filled.get("groupid") is not None:
                    self._fields["groupid"].setText(str(filled["groupid"]))
            elif self.network == "exoclock":
                self._fields["target"].setText(str(filled.get("target") or ""))
                if filled.get("observer"):
                    self._fields["observer"].setText(str(filled["observer"]))
            elif self.network == "bess":
                self._fields["objname"].setText(str(filled.get("objname") or ""))
                self._fields["observer"].setText(str(filled.get("observer") or ""))
                self._fields["date_obs"].setText(str(filled.get("date_obs") or ""))
            elif self.network == "iota":
                self._fields["event_id"].setText(str(filled.get("event_id") or ""))
                self._fields["star"].setText(str(filled.get("star") or ""))
                self._fields["asteroid"].setText(str(filled.get("asteroid") or ""))
                self._fields["observer"].setText(str(filled.get("observer") or ""))
                res = str(filled.get("result") or "positive")
                ri = self._fields["result"].findText(res)
                if ri >= 0:
                    self._fields["result"].setCurrentIndex(ri)
            elif self.network == "cobs":
                self._fields["designation"].setText(str(filled.get("designation") or ""))
                self._fields["epoch_utc"].setText(str(filled.get("epoch_utc") or ""))
                if filled.get("mag") is not None:
                    self._fields["mag"].setValue(float(filled["mag"]))
                self._fields["mag_method"].setText(str(filled.get("mag_method") or "B"))
                self._fields["comp_cat"].setText(str(filled.get("comp_cat") or ""))
                if filled.get("aperture_cm") is not None:
                    self._fields["aperture_cm"].setValue(float(filled["aperture_cm"]))
                self._fields["instr_type"].setText(str(filled.get("instr_type") or "L"))
                if filled.get("coma_arcmin") is not None:
                    self._fields["coma_arcmin"].setValue(float(filled["coma_arcmin"]))
                self._fields["dc"].setText(str(filled.get("dc") or ""))
                self._fields["obscode"].setText(str(filled.get("obscode") or ""))
                self._fields["observer"].setText(str(filled.get("observer") or ""))
                self._fields["location"].setText(str(filled.get("location") or ""))
                self._fields["notes"].setText(str(filled.get("notes") or ""))
            else:
                self._fields["designation"].setText(
                    str(filled.get("designation") or "")
                )
                self._fields["epoch_utc"].setText(str(filled.get("epoch_utc") or ""))
                if filled.get("ra_deg") is not None:
                    self._fields["ra_deg"].setValue(float(filled["ra_deg"]))
                if filled.get("dec_deg") is not None:
                    self._fields["dec_deg"].setValue(float(filled["dec_deg"]))
                if filled.get("mag") is not None:
                    self._fields["mag"].setValue(float(filled["mag"]))
                self._fields["band"].setText(str(filled.get("band") or "R"))

        def _prefill_from_product(self) -> None:
            vals = self.values()
            prefills = {
                "aavso": prefill_aavso_fields,
                "wds": prefill_wds_fields,
                "mpc": prefill_mpc_fields,
                "tns": prefill_tns_fields,
                "exoclock": prefill_exoclock_fields,
                "bess": prefill_bess_fields,
                "iota": prefill_iota_fields,
                "cobs": prefill_cobs_fields,
            }
            fn = prefills.get(self.network, prefill_mpc_fields)
            filled = fn(self.archive, credentials={}, current=vals)
            self._apply_filled(filled)
            self._run_check()

        def _run_check(self) -> Any:
            vals = self.values()
            pid = _parse_uuid(vals.get("product_id"))
            if self.network == "aavso":
                result = validate_product_for_network(
                    self.archive,
                    network="aavso",
                    product_id=pid,
                    payload={
                        "obscode": vals.get("obscode"),
                        "star": vals.get("star"),
                    },
                )
            elif self.network == "wds":
                result = validate_product_for_network(
                    self.archive,
                    network="wds",
                    product_id=pid,
                    payload={"object": vals.get("object")},
                )
            elif self.network == "tns":
                result = validate_product_for_network(
                    self.archive,
                    network="tns",
                    product_id=pid,
                    payload={
                        "ra_deg": vals.get("ra_deg"),
                        "dec_deg": vals.get("dec_deg"),
                    },
                )
            elif self.network == "exoclock":
                result = validate_product_for_network(
                    self.archive,
                    network="exoclock",
                    product_id=pid,
                    payload={"target": vals.get("target")},
                )
            elif self.network == "bess":
                result = validate_product_for_network(
                    self.archive,
                    network="bess",
                    product_id=pid,
                    payload={
                        "observer": vals.get("observer"),
                        "objname": vals.get("objname"),
                        "date_obs": vals.get("date_obs"),
                    },
                )
            elif self.network == "iota":
                result = validate_product_for_network(
                    self.archive,
                    network="iota",
                    product_id=pid,
                    payload={
                        "event_id": vals.get("event_id"),
                        "star": vals.get("star"),
                        "asteroid": vals.get("asteroid"),
                        "observer": vals.get("observer"),
                    },
                )
            elif self.network == "cobs":
                result = validate_product_for_network(
                    self.archive,
                    network="cobs",
                    product_id=pid,
                    payload={
                        "designation": vals.get("designation"),
                        "epoch_utc": vals.get("epoch_utc"),
                        "mag": vals.get("mag"),
                        "mag_method": vals.get("mag_method"),
                        "obscode": vals.get("obscode"),
                    },
                )
            else:
                result = validate_product_for_network(
                    self.archive,
                    network="mpc",
                    product_id=pid,
                    payload={
                        "observatory_code": vals.get("observatory_code"),
                        "designation": vals.get("designation"),
                        "ra_deg": vals.get("ra_deg"),
                        "dec_deg": vals.get("dec_deg"),
                        "epoch_utc": vals.get("epoch_utc"),
                    },
                )
            self.issues.clear()
            for line in format_validation_issue_lines(result):
                self.issues.addItem(line)
            if result.ok:
                self.status.setText("OK — campos minimos do atlas satisfeitos.")
            else:
                self.status.setText(
                    "Erros bloqueiam Aceitar. Corrija ou preencha do produto."
                )
            return result

        def _on_accept(self) -> None:
            result = self._run_check()
            if not result.ok:
                QMessageBox.warning(
                    self,
                    "Validacao",
                    "\n".join(result.error_messages()) or "Campos incompletos.",
                )
                return
            self.accept()

    class ContributeDashboard(QWidget):
        def __init__(self, archive: Any, *, artifacts_root: Path | None = None) -> None:
            super().__init__(parent)
            self.archive = archive
            self.artifacts_root = Path(artifacts_root or default_artifacts_root())
            self.creds = LocalCredentialsStore()
            self._workspace_id: UUID | None = None

            root = QVBoxLayout(self)
            top = QHBoxLayout()
            self.filter_combo = QComboBox()
            self.filter_combo.addItem("Todas", None)
            for n in ("aavso", "mpc", "tns", "bess", "exoclock", "iota", "wds", "cobs"):
                self.filter_combo.addItem(n, n)
            self.refresh_btn = QPushButton("Atualizar lista")
            self.refresh_btn.clicked.connect(self.refresh)
            top.addWidget(QLabel("Rede"))
            top.addWidget(self.filter_combo)
            top.addWidget(self.refresh_btn)
            top.addStretch(1)
            root.addLayout(top)

            self.cred_label = QLabel()
            self.cred_label.setWordWrap(True)
            root.addWidget(self.cred_label)

            self.table = QTableWidget(0, 5)
            self.table.setHorizontalHeaderLabels(
                ["Quando", "Rede", "Estado", "Id", "Artefacto"]
            )
            root.addWidget(self.table, 1)

            tabs = QTabWidget()
            tabs.addTab(self._tab_aavso(), "AAVSO")
            tabs.addTab(self._tab_mpc(), "MPC")
            tabs.addTab(self._tab_wds(), "WDS")
            tabs.addTab(self._tab_cobs(), "COBS")
            tabs.addTab(self._tab_tns(), "TNS")
            tabs.addTab(self._tab_bess(), "BeSS")
            tabs.addTab(self._tab_exoclock(), "ExoClock")
            tabs.addTab(self._tab_iota(), "IOTA")
            self.export_tabs = tabs
            root.addWidget(tabs)

            self.log = QTextEdit()
            self.log.setReadOnly(True)
            self.log.setMaximumHeight(90)
            root.addWidget(self.log)

        def _tab_aavso(self) -> QWidget:
            from PySide6.QtCore import QUrl
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtWidgets import QLabel

            from astrocitizen.adapters.aavso_portal import WEBOBS_URL

            w = QWidget()
            form = QFormLayout(w)
            self.a_product = QLineEdit()
            self.a_star = QLineEdit()
            self.a_star.setText("SS CYG")
            self.a_obscode = QLineEdit()
            self.a_band = QLineEdit()
            self.a_band.setText("V")
            self.a_chart = QLineEdit()
            self.a_chart.setText("NA")
            hint = QLabel(
                "Upload manual no WebObs — metodo oficial AAVSO "
                "(AEF validado; sem API de submissao)."
            )
            hint.setObjectName("emptyState")
            hint.setWordWrap(True)
            review = QPushButton("Revisar campos")
            review.clicked.connect(lambda: self._review_fields("aavso"))
            btn = QPushButton("Gerar AEF e preparar WebObs")
            btn.clicked.connect(self._run_aavso)
            self.a_open_webobs = QPushButton("Abrir WebObs")
            self.a_open_webobs.setObjectName("secondaryBtn")
            self.a_open_webobs.setEnabled(False)
            self.a_open_webobs.clicked.connect(
                lambda: QDesktopServices.openUrl(QUrl(WEBOBS_URL))
            )
            self.a_open_aef = QPushButton("Abrir ficheiro AEF")
            self.a_open_aef.setObjectName("secondaryBtn")
            self.a_open_aef.setEnabled(False)
            self.a_open_aef.clicked.connect(self._open_last_aef)
            self._last_aef_path: Path | None = None
            form.addRow(hint)
            form.addRow("Product UUID", self.a_product)
            form.addRow("Star", self.a_star)
            form.addRow("OBSCODE", self.a_obscode)
            form.addRow("Band", self.a_band)
            form.addRow("Chart", self.a_chart)
            row = QHBoxLayout()
            row.addWidget(review)
            row.addWidget(btn)
            form.addRow(row)
            row2 = QHBoxLayout()
            row2.addWidget(self.a_open_webobs)
            row2.addWidget(self.a_open_aef)
            form.addRow(row2)
            return w

        def _open_last_aef(self) -> None:
            from PySide6.QtCore import QUrl
            from PySide6.QtGui import QDesktopServices

            if self._last_aef_path is None or not self._last_aef_path.is_file():
                QMessageBox.information(
                    self, "AAVSO", "Gere o AEF primeiro (Gerar AEF e preparar WebObs)."
                )
                return
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._last_aef_path)))

        def _tab_mpc(self) -> QWidget:
            w = QWidget()
            form = QFormLayout(w)
            self.m_product = QLineEdit()
            self.m_desig = QLineEdit()
            self.m_code = QLineEdit()
            self.m_epoch = QLineEdit()
            self.m_epoch.setText("2026-07-21T02:30:00Z")
            self.m_ra = QDoubleSpinBox()
            self.m_ra.setRange(0, 360)
            self.m_ra.setDecimals(6)
            self.m_dec = QDoubleSpinBox()
            self.m_dec.setRange(-90, 90)
            self.m_dec.setDecimals(6)
            self.m_mag = QDoubleSpinBox()
            self.m_mag.setRange(-1, 30)
            self.m_mag.setDecimals(3)
            self.m_mag.setSpecialValueText("(vazio)")
            self.m_mag.setValue(-1)
            self.m_band = QLineEdit()
            self.m_band.setText("R")
            self.m_email = QLineEdit()
            self.m_submit = QComboBox()
            self.m_submit.addItem("Dry-run", False)
            self.m_submit.addItem("Submit real", True)
            review = QPushButton("Revisar campos")
            review.clicked.connect(lambda: self._review_fields("mpc"))
            btn = QPushButton("ADES PSV")
            btn.clicked.connect(self._run_mpc)
            form.addRow("Product UUID", self.m_product)
            form.addRow("Designation", self.m_desig)
            form.addRow("Obs code", self.m_code)
            form.addRow("Epoch UTC", self.m_epoch)
            form.addRow("RA deg", self.m_ra)
            form.addRow("Dec deg", self.m_dec)
            form.addRow("Mag", self.m_mag)
            form.addRow("Band", self.m_band)
            form.addRow("Email", self.m_email)
            form.addRow("Modo", self.m_submit)
            row = QHBoxLayout()
            row.addWidget(review)
            row.addWidget(btn)
            form.addRow(row)
            return w

        def _tab_wds(self) -> QWidget:
            w = QWidget()
            form = QFormLayout(w)
            self.w_product = QLineEdit()
            self.w_object = QLineEdit()
            self.w_epoch = QLineEdit()
            self.w_pa = QDoubleSpinBox()
            self.w_pa.setRange(0, 359.999)
            self.w_pa.setDecimals(3)
            self.w_sep = QDoubleSpinBox()
            self.w_sep.setRange(0.001, 9999)
            self.w_sep.setDecimals(3)
            self.w_sep.setValue(1.0)
            self.w_mag1 = QDoubleSpinBox()
            self.w_mag1.setRange(-1, 30)
            self.w_mag1.setDecimals(2)
            self.w_mag1.setSpecialValueText("(vazio)")
            self.w_mag1.setValue(-1)
            self.w_mag2 = QDoubleSpinBox()
            self.w_mag2.setRange(-1, 30)
            self.w_mag2.setDecimals(2)
            self.w_mag2.setSpecialValueText("(vazio)")
            self.w_mag2.setValue(-1)
            self.w_method = QComboBox()
            for m in ("micrometer", "imaging_manual", "other"):
                self.w_method.addItem(m, m)
            self.w_observer = QLineEdit()
            self.w_observatory = QLineEdit()
            review = QPushButton("Revisar campos")
            review.clicked.connect(lambda: self._review_fields("wds"))
            btn = QPushButton("Export EXP-WDS")
            btn.clicked.connect(self._run_wds)
            form.addRow("Product UUID", self.w_product)
            form.addRow("WDS / object", self.w_object)
            form.addRow("Epoch UTC", self.w_epoch)
            form.addRow("PA deg", self.w_pa)
            form.addRow("Sep arcsec", self.w_sep)
            form.addRow("Mag1", self.w_mag1)
            form.addRow("Mag2", self.w_mag2)
            form.addRow("Method", self.w_method)
            form.addRow("Observer", self.w_observer)
            form.addRow("Observatory", self.w_observatory)
            row = QHBoxLayout()
            row.addWidget(review)
            row.addWidget(btn)
            form.addRow(row)
            return w

        def _tab_cobs(self) -> QWidget:
            w = QWidget()
            form = QFormLayout(w)
            self.c_product = QLineEdit()
            self.c_desig = QLineEdit()
            self.c_epoch = QLineEdit()
            self.c_mag = QDoubleSpinBox()
            self.c_mag.setRange(-5.1, 25)
            self.c_mag.setDecimals(1)
            self.c_mag.setSpecialValueText("(vazio)")
            self.c_mag.setValue(-5.1)
            self.c_method = QLineEdit()
            self.c_method.setText("B")
            self.c_aperture = QDoubleSpinBox()
            self.c_aperture.setRange(0, 999)
            self.c_aperture.setDecimals(1)
            self.c_aperture.setSpecialValueText("(vazio)")
            self.c_aperture.setValue(0)
            self.c_obscode = QLineEdit()
            self.c_observer = QLineEdit()
            self.c_location = QLineEdit()
            review = QPushButton("Revisar campos")
            review.clicked.connect(lambda: self._review_fields("cobs"))
            btn = QPushButton("Export EXP-COBS")
            btn.clicked.connect(self._run_cobs)
            form.addRow("Product UUID", self.c_product)
            form.addRow("Designation", self.c_desig)
            form.addRow("Epoch UTC", self.c_epoch)
            form.addRow("Mag", self.c_mag)
            form.addRow("Mag method", self.c_method)
            form.addRow("Aperture cm", self.c_aperture)
            form.addRow("OBSCODE", self.c_obscode)
            form.addRow("Observer", self.c_observer)
            form.addRow("Location", self.c_location)
            row = QHBoxLayout()
            row.addWidget(review)
            row.addWidget(btn)
            form.addRow(row)
            return w

        def _tab_tns(self) -> QWidget:
            w = QWidget()
            form = QFormLayout(w)
            self.t_product = QLineEdit()
            self.t_ra = QDoubleSpinBox()
            self.t_ra.setRange(0, 360)
            self.t_ra.setDecimals(6)
            self.t_dec = QDoubleSpinBox()
            self.t_dec.setRange(-90, 90)
            self.t_dec.setDecimals(6)
            self.t_mag = QDoubleSpinBox()
            self.t_mag.setRange(0, 30)
            self.t_mag.setDecimals(3)
            self.t_mag.setValue(19.0)
            self.t_group = QLineEdit()
            self.t_group.setText("0")
            self.t_submit = QComboBox()
            self.t_submit.addItem("Dry-run sandbox", False)
            self.t_submit.addItem("Submit sandbox", True)
            review = QPushButton("Revisar campos")
            review.clicked.connect(lambda: self._review_fields("tns"))
            btn = QPushButton("TNS AT-rep")
            btn.clicked.connect(self._run_tns)
            form.addRow("Product UUID", self.t_product)
            form.addRow("RA deg", self.t_ra)
            form.addRow("Dec deg", self.t_dec)
            form.addRow("Mag", self.t_mag)
            form.addRow("Group id", self.t_group)
            form.addRow("Modo", self.t_submit)
            row = QHBoxLayout()
            row.addWidget(review)
            row.addWidget(btn)
            form.addRow(row)
            return w

        def _tab_bess(self) -> QWidget:
            w = QWidget()
            form = QFormLayout(w)
            self.b_product = QLineEdit()
            self.b_obj = QLineEdit()
            self.b_obj.setText("gam Cas")
            self.b_obs = QLineEdit()
            self.b_date = QLineEdit()
            self.b_date.setText("2026-07-21T01:00:00")
            review = QPushButton("Revisar campos")
            review.clicked.connect(lambda: self._review_fields("bess"))
            btn = QPushButton("Gerar FITS 1D BeSS")
            btn.clicked.connect(self._run_bess)
            form.addRow("Product UUID", self.b_product)
            form.addRow("OBJNAME", self.b_obj)
            form.addRow("Observer", self.b_obs)
            form.addRow("DATE-OBS", self.b_date)
            row = QHBoxLayout()
            row.addWidget(review)
            row.addWidget(btn)
            form.addRow(row)
            return w

        def _tab_exoclock(self) -> QWidget:
            w = QWidget()
            form = QFormLayout(w)
            self.e_product = QLineEdit()
            self.e_target = QLineEdit()
            self.e_target.setText("WASP-12b")
            review = QPushButton("Revisar campos")
            review.clicked.connect(lambda: self._review_fields("exoclock"))
            btn = QPushButton("Export LC ExoClock")
            btn.clicked.connect(self._run_exoclock)
            form.addRow("Product UUID", self.e_product)
            form.addRow("Target", self.e_target)
            row = QHBoxLayout()
            row.addWidget(review)
            row.addWidget(btn)
            form.addRow(row)
            return w

        def _tab_iota(self) -> QWidget:
            w = QWidget()
            form = QFormLayout(w)
            self.i_product = QLineEdit()
            self.i_event = QLineEdit()
            self.i_star = QLineEdit()
            self.i_ast = QLineEdit()
            self.i_obs = QLineEdit()
            self.i_result = QComboBox()
            self.i_result.addItems(["positive", "negative"])
            review = QPushButton("Revisar campos")
            review.clicked.connect(lambda: self._review_fields("iota"))
            btn = QPushButton("Pacote IOTA-ES")
            btn.clicked.connect(self._run_iota)
            form.addRow("Product UUID", self.i_product)
            form.addRow("Event ID", self.i_event)
            form.addRow("Star", self.i_star)
            form.addRow("Asteroid", self.i_ast)
            form.addRow("Observer", self.i_obs)
            form.addRow("Result", self.i_result)
            row = QHBoxLayout()
            row.addWidget(review)
            row.addWidget(btn)
            form.addRow(row)
            return w

        def load_workspace(self) -> None:
            workspaces = self.archive.list_workspaces()
            self._workspace_id = workspaces[0].id if workspaces else None
            a_cred = self.creds.get_network("aavso")
            if a_cred.get("obscode") and not self.a_obscode.text():
                self.a_obscode.setText(str(a_cred["obscode"]))
            m_cred = self.creds.get_network("mpc")
            if m_cred.get("observatory_code") and not self.m_code.text():
                self.m_code.setText(str(m_cred["observatory_code"]))
            if m_cred.get("email") and not self.m_email.text():
                self.m_email.setText(str(m_cred["email"]))
            w_cred = self.creds.get_network("wds")
            if w_cred.get("observer") and not self.w_observer.text():
                self.w_observer.setText(str(w_cred["observer"]))
            c_cred = self.creds.get_network("cobs")
            if c_cred.get("obscode") and not self.c_obscode.text():
                self.c_obscode.setText(str(c_cred["obscode"]))
            if c_cred.get("observer") and not self.c_observer.text():
                self.c_observer.setText(str(c_cred["observer"]))
            t_cred = self.creds.get_network("tns")
            if t_cred.get("groupid") is not None and self.t_group.text() == "0":
                self.t_group.setText(str(t_cred["groupid"]))
            for net, widget in (
                ("bess", self.b_obs),
                ("exoclock", None),
                ("iota", self.i_obs),
            ):
                cred = self.creds.get_network(net)
                if widget is not None and cred.get("observer") and not widget.text():
                    widget.setText(str(cred["observer"]))
            self.refresh()

        def refresh(self) -> None:
            self.cred_label.setText(" | ".join(credentials_status_lines(self.creds)))
            if self._workspace_id is None:
                self.table.setRowCount(0)
                return
            net = self.filter_combo.currentData()
            subs = self.archive.list_network_submissions(self._workspace_id, network=net)
            rows = submission_table_rows(subs)
            self.table.setRowCount(len(rows))
            for r, row in enumerate(rows):
                for c, val in enumerate(row):
                    self.table.setItem(r, c, QTableWidgetItem(val))
            self.table.resizeColumnsToContents()

        def focus_network(
            self, network: str | None = None, *, product_id: str | None = None
        ) -> None:
            """Filtra lista e abre tab de export da rede (ex.: aavso)."""
            if network:
                key = str(network).lower()
                i = self.filter_combo.findData(key)
                if i >= 0:
                    self.filter_combo.setCurrentIndex(i)
                titles = {
                    "aavso": "AAVSO",
                    "mpc": "MPC",
                    "wds": "WDS",
                    "cobs": "COBS",
                    "tns": "TNS",
                    "bess": "BeSS",
                    "exoclock": "ExoClock",
                    "iota": "IOTA",
                }
                title = titles.get(key)
                if title and hasattr(self, "export_tabs"):
                    for ti in range(self.export_tabs.count()):
                        if self.export_tabs.tabText(ti) == title:
                            self.export_tabs.setCurrentIndex(ti)
                            break
            if product_id:
                pid = str(product_id).strip()
                for edit_name in (
                    "a_product",
                    "m_product",
                    "w_product",
                    "c_product",
                    "t_product",
                    "e_product",
                    "b_product",
                    "i_product",
                ):
                    edit = getattr(self, edit_name, None)
                    if edit is not None and hasattr(edit, "setText"):
                        edit.setText(pid)
            self.refresh()

        def _log(self, msg: str) -> None:
            self.log.append(msg)

        def _aavso_current(self) -> dict[str, Any]:
            return {
                "product_id": self.a_product.text().strip(),
                "star": self.a_star.text().strip(),
                "obscode": self.a_obscode.text().strip(),
                "band": self.a_band.text().strip() or "V",
                "chart": self.a_chart.text().strip() or "NA",
            }

        def _mpc_current(self) -> dict[str, Any]:
            mag_val = float(self.m_mag.value())
            return {
                "product_id": self.m_product.text().strip(),
                "designation": self.m_desig.text().strip(),
                "observatory_code": self.m_code.text().strip(),
                "epoch_utc": self.m_epoch.text().strip(),
                "ra_deg": float(self.m_ra.value()),
                "dec_deg": float(self.m_dec.value()),
                "mag": None if mag_val < 0 else mag_val,
                "band": self.m_band.text().strip() or "R",
                "email": self.m_email.text().strip(),
            }

        def _wds_current(self) -> dict[str, Any]:
            m1 = float(self.w_mag1.value())
            m2 = float(self.w_mag2.value())
            return {
                "product_id": self.w_product.text().strip(),
                "object": self.w_object.text().strip(),
                "epoch_utc": self.w_epoch.text().strip(),
                "pa_deg": float(self.w_pa.value()),
                "sep_arcsec": float(self.w_sep.value()),
                "mag_primary": None if m1 < 0 else m1,
                "mag_secondary": None if m2 < 0 else m2,
                "method": str(self.w_method.currentData() or self.w_method.currentText()),
                "observer": self.w_observer.text().strip(),
                "observatory": self.w_observatory.text().strip(),
            }

        def _apply_aavso_fields(self, vals: dict[str, Any]) -> None:
            self.a_product.setText(str(vals.get("product_id") or ""))
            self.a_star.setText(str(vals.get("star") or ""))
            self.a_obscode.setText(str(vals.get("obscode") or ""))
            self.a_band.setText(str(vals.get("band") or "V"))
            self.a_chart.setText(str(vals.get("chart") or "NA"))

        def _apply_mpc_fields(self, vals: dict[str, Any]) -> None:
            self.m_product.setText(str(vals.get("product_id") or ""))
            self.m_desig.setText(str(vals.get("designation") or ""))
            self.m_code.setText(str(vals.get("observatory_code") or ""))
            self.m_epoch.setText(str(vals.get("epoch_utc") or ""))
            if vals.get("ra_deg") is not None:
                self.m_ra.setValue(float(vals["ra_deg"]))
            if vals.get("dec_deg") is not None:
                self.m_dec.setValue(float(vals["dec_deg"]))
            if vals.get("mag") is not None:
                self.m_mag.setValue(float(vals["mag"]))
            else:
                self.m_mag.setValue(-1)
            self.m_band.setText(str(vals.get("band") or "R"))
            if vals.get("email"):
                self.m_email.setText(str(vals["email"]))

        def _apply_wds_fields(self, vals: dict[str, Any]) -> None:
            self.w_product.setText(str(vals.get("product_id") or ""))
            self.w_object.setText(str(vals.get("object") or ""))
            self.w_epoch.setText(str(vals.get("epoch_utc") or ""))
            if vals.get("pa_deg") is not None:
                self.w_pa.setValue(float(vals["pa_deg"]))
            if vals.get("sep_arcsec") is not None:
                self.w_sep.setValue(float(vals["sep_arcsec"]))
            if vals.get("mag_primary") is not None:
                self.w_mag1.setValue(float(vals["mag_primary"]))
            else:
                self.w_mag1.setValue(-1)
            if vals.get("mag_secondary") is not None:
                self.w_mag2.setValue(float(vals["mag_secondary"]))
            else:
                self.w_mag2.setValue(-1)
            meth = str(vals.get("method") or "micrometer")
            mi = self.w_method.findData(meth)
            if mi >= 0:
                self.w_method.setCurrentIndex(mi)
            self.w_observer.setText(str(vals.get("observer") or ""))
            self.w_observatory.setText(str(vals.get("observatory") or ""))

        def _tns_current(self) -> dict[str, Any]:
            return {
                "product_id": self.t_product.text().strip(),
                "ra_deg": float(self.t_ra.value()),
                "dec_deg": float(self.t_dec.value()),
                "mag": float(self.t_mag.value()),
                "groupid": self.t_group.text().strip() or "0",
            }

        def _exoclock_current(self) -> dict[str, Any]:
            return {
                "product_id": self.e_product.text().strip(),
                "target": self.e_target.text().strip(),
                "observer": str(
                    self.creds.get_network("exoclock").get("observer") or ""
                ),
            }

        def _bess_current(self) -> dict[str, Any]:
            return {
                "product_id": self.b_product.text().strip(),
                "objname": self.b_obj.text().strip(),
                "observer": self.b_obs.text().strip(),
                "date_obs": self.b_date.text().strip(),
            }

        def _iota_current(self) -> dict[str, Any]:
            return {
                "product_id": self.i_product.text().strip(),
                "event_id": self.i_event.text().strip(),
                "star": self.i_star.text().strip(),
                "asteroid": self.i_ast.text().strip(),
                "observer": self.i_obs.text().strip(),
                "result": self.i_result.currentText(),
            }

        def _apply_tns_fields(self, vals: dict[str, Any]) -> None:
            self.t_product.setText(str(vals.get("product_id") or ""))
            if vals.get("ra_deg") is not None:
                self.t_ra.setValue(float(vals["ra_deg"]))
            if vals.get("dec_deg") is not None:
                self.t_dec.setValue(float(vals["dec_deg"]))
            if vals.get("mag") is not None:
                self.t_mag.setValue(float(vals["mag"]))
            if vals.get("groupid") is not None:
                self.t_group.setText(str(vals["groupid"]))

        def _apply_exoclock_fields(self, vals: dict[str, Any]) -> None:
            self.e_product.setText(str(vals.get("product_id") or ""))
            self.e_target.setText(str(vals.get("target") or ""))

        def _apply_bess_fields(self, vals: dict[str, Any]) -> None:
            self.b_product.setText(str(vals.get("product_id") or ""))
            self.b_obj.setText(str(vals.get("objname") or ""))
            self.b_obs.setText(str(vals.get("observer") or ""))
            self.b_date.setText(str(vals.get("date_obs") or ""))

        def _apply_iota_fields(self, vals: dict[str, Any]) -> None:
            self.i_product.setText(str(vals.get("product_id") or ""))
            self.i_event.setText(str(vals.get("event_id") or ""))
            self.i_star.setText(str(vals.get("star") or ""))
            self.i_ast.setText(str(vals.get("asteroid") or ""))
            self.i_obs.setText(str(vals.get("observer") or ""))
            res = str(vals.get("result") or "positive")
            ri = self.i_result.findText(res)
            if ri >= 0:
                self.i_result.setCurrentIndex(ri)

        def _cobs_current(self) -> dict[str, Any]:
            mag_val = float(self.c_mag.value())
            ap = float(self.c_aperture.value())
            return {
                "product_id": self.c_product.text().strip(),
                "designation": self.c_desig.text().strip(),
                "epoch_utc": self.c_epoch.text().strip(),
                "mag": None if mag_val < -5 else mag_val,
                "mag_method": self.c_method.text().strip() or "B",
                "aperture_cm": None if ap <= 0 else ap,
                "obscode": self.c_obscode.text().strip(),
                "observer": self.c_observer.text().strip(),
                "location": self.c_location.text().strip(),
            }

        def _apply_cobs_fields(self, vals: dict[str, Any]) -> None:
            self.c_product.setText(str(vals.get("product_id") or ""))
            self.c_desig.setText(str(vals.get("designation") or ""))
            self.c_epoch.setText(str(vals.get("epoch_utc") or ""))
            if vals.get("mag") is not None:
                self.c_mag.setValue(float(vals["mag"]))
            else:
                self.c_mag.setValue(-5.1)
            self.c_method.setText(str(vals.get("mag_method") or "B"))
            if vals.get("aperture_cm") is not None:
                self.c_aperture.setValue(float(vals["aperture_cm"]))
            else:
                self.c_aperture.setValue(0)
            self.c_obscode.setText(str(vals.get("obscode") or ""))
            self.c_observer.setText(str(vals.get("observer") or ""))
            self.c_location.setText(str(vals.get("location") or ""))

        def _save_review_draft(
            self, *, network: str, vals: dict[str, Any], product_id: UUID | None
        ) -> None:
            if self._workspace_id is None:
                return
            summary = dict(vals)
            summary["note"] = "revisao atlas"
            sub = NetworkSubmission(
                id=new_id(),
                workspace_id=self._workspace_id,
                network=network,
                status="draft",
                product_id=product_id,
                payload_summary=summary,
            )
            self.archive.save_network_submission(sub)
            self._log(f"{network.upper()} rascunho revisado {sub.id}")
            self.refresh()

        def _review_fields(self, network: str) -> None:
            builders = {
                "aavso": (prefill_aavso_fields, self._aavso_current, self._apply_aavso_fields),
                "mpc": (prefill_mpc_fields, self._mpc_current, self._apply_mpc_fields),
                "wds": (prefill_wds_fields, self._wds_current, self._apply_wds_fields),
                "tns": (prefill_tns_fields, self._tns_current, self._apply_tns_fields),
                "exoclock": (
                    prefill_exoclock_fields,
                    self._exoclock_current,
                    self._apply_exoclock_fields,
                ),
                "bess": (prefill_bess_fields, self._bess_current, self._apply_bess_fields),
                "iota": (prefill_iota_fields, self._iota_current, self._apply_iota_fields),
                "cobs": (prefill_cobs_fields, self._cobs_current, self._apply_cobs_fields),
            }
            prefill_fn, current_fn, apply_fn = builders[network]
            initial = prefill_fn(
                self.archive,
                credentials=self.creds.get_network(network),
                current=current_fn(),
            )
            dlg = FieldReviewDialog(
                self, network=network, archive=self.archive, initial=initial
            )
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
            vals = dlg.values()
            apply_fn(vals)
            self._save_review_draft(
                network=network,
                vals=vals,
                product_id=_parse_uuid(vals.get("product_id")),
            )

        def _run_aavso(self) -> None:
            from astrocitizen.adapters.aavso_portal import WEBOBS_URL

            if self._workspace_id is None:
                QMessageBox.warning(self, "Contribute", "Sem workspace.")
                return
            try:
                pid = UUID(self.a_product.text().strip())
            except ValueError:
                QMessageBox.warning(self, "AAVSO", "Product UUID invalido.")
                return
            obscode = self.a_obscode.text().strip() or self.creds.get_network("aavso").get(
                "obscode"
            )
            if not obscode:
                QMessageBox.warning(self, "AAVSO", "Falta OBSCODE.")
                return
            star = self.a_star.text().strip() or "UNKNOWN"
            chart = self.a_chart.text().strip() or "NA"
            check = validate_product_for_network(
                self.archive,
                network="aavso",
                product_id=pid,
                payload={"obscode": obscode, "star": star, "chart": chart},
            )
            for issue in check.issues:
                if issue.severity == "warning":
                    self._log(f"aviso AAVSO: {issue.message}")
            if not check.ok:
                QMessageBox.warning(
                    self,
                    "Validacao AAVSO",
                    "\n".join(check.error_messages()) or "Produto incompleto.",
                )
                return
            out = self.artifacts_root / "export" / "aavso" / f"{pid}.txt"
            try:
                ExportAavso(self.archive).execute(
                    product_id=pid,
                    star_name=star,
                    observer_code=str(obscode),
                    out_path=out,
                    band=self.a_band.text().strip() or "V",
                    chart=chart,
                )
                store = LocalArtifactStore(self.artifacts_root)
                uri = store.put(out, key=f"export/aavso/{out.name}")
                sub = NetworkSubmission(
                    id=new_id(),
                    workspace_id=self._workspace_id,
                    network="aavso",
                    status="validated",
                    artifact_uri=uri,
                    product_id=pid,
                    payload_summary={
                        "star": star,
                        "chart": chart,
                        "note": "WebObs manual (oficial)",
                    },
                )
                self.archive.save_network_submission(sub)
                self._last_aef_path = out
                self.a_open_webobs.setEnabled(True)
                self.a_open_aef.setEnabled(True)
                self._log(
                    f"AAVSO AEF pronto: {out} — upload manual em {WEBOBS_URL}"
                )
                self.refresh()
            except Exception as exc:  # noqa: BLE001
                QMessageBox.critical(self, "AAVSO", str(exc))

        def _run_mpc(self) -> None:
            if self._workspace_id is None:
                QMessageBox.warning(self, "Contribute", "Sem workspace.")
                return
            code = self.m_code.text().strip() or self.creds.get_network("mpc").get(
                "observatory_code"
            )
            if not code or not self.m_desig.text().strip():
                QMessageBox.warning(self, "MPC", "Designation e obs code obrigatorios.")
                return
            product_id = _parse_uuid(self.m_product.text())
            mag_val = float(self.m_mag.value())
            mag = None if mag_val < 0 else mag_val
            band = self.m_band.text().strip() or "R"
            check = validate_product_for_network(
                self.archive,
                network="mpc",
                product_id=product_id,
                payload={
                    "observatory_code": code,
                    "designation": self.m_desig.text().strip(),
                    "ra_deg": float(self.m_ra.value()),
                    "dec_deg": float(self.m_dec.value()),
                    "epoch_utc": self.m_epoch.text().strip(),
                },
            )
            if not check.ok:
                QMessageBox.warning(
                    self,
                    "Validacao MPC",
                    "\n".join(check.error_messages()) or "Campos incompletos.",
                )
                return
            out = self.artifacts_root / "export" / "mpc" / "gui.psv"
            try:
                obs: dict[str, Any] = {
                    "epoch_utc": self.m_epoch.text().strip(),
                    "ra_deg": float(self.m_ra.value()),
                    "dec_deg": float(self.m_dec.value()),
                    "band": band,
                }
                if mag is not None:
                    obs["mag"] = mag
                write_ades_psv(
                    out,
                    observatory_code=str(code),
                    designation=self.m_desig.text().strip(),
                    observations=[obs],
                )
                email = self.m_email.text().strip() or self.creds.get_network("mpc").get(
                    "email"
                )
                do_submit = bool(self.m_submit.currentData())
                if do_submit and not email:
                    QMessageBox.warning(self, "MPC", "Submit real requer email.")
                    return
                meta = MpcAdesSubmitter().submit(
                    out,
                    email=str(email or "dry-run@example.com"),
                    dry_run=not do_submit,
                )
                store = LocalArtifactStore(self.artifacts_root)
                uri = store.put(out, key=f"export/mpc/{out.name}")
                sub = NetworkSubmission(
                    id=new_id(),
                    workspace_id=self._workspace_id,
                    network="mpc",
                    status=str(meta.get("status") or "draft"),
                    artifact_uri=uri,
                    product_id=product_id,
                    payload_summary={
                        "designation": self.m_desig.text(),
                        "meta": meta,
                    },
                    remote_ack=str(meta.get("response") or meta.get("ack") or "")[:500]
                    or None,
                )
                self.archive.save_network_submission(sub)
                self._log(f"MPC {sub.status} {out}")
                self.refresh()
            except Exception as exc:  # noqa: BLE001
                QMessageBox.critical(self, "MPC", str(exc))

        def _run_wds(self) -> None:
            if self._workspace_id is None:
                QMessageBox.warning(self, "Contribute", "Sem workspace.")
                return
            try:
                pid = UUID(self.w_product.text().strip())
            except ValueError:
                QMessageBox.warning(self, "WDS", "Product UUID invalido.")
                return
            obj = self.w_object.text().strip()
            check = validate_product_for_network(
                self.archive,
                network="wds",
                product_id=pid,
                payload={"object": obj},
            )
            if not check.ok:
                QMessageBox.warning(
                    self,
                    "Validacao WDS",
                    "\n".join(check.error_messages()) or "Produto incompleto.",
                )
                return
            m1 = float(self.w_mag1.value())
            m2 = float(self.w_mag2.value())
            overrides: dict[str, Any] = {
                "object_name": obj or None,
                "epoch_utc": self.w_epoch.text().strip() or None,
                "pa_deg": float(self.w_pa.value()),
                "sep_arcsec": float(self.w_sep.value()),
                "method": str(
                    self.w_method.currentData() or self.w_method.currentText()
                ),
                "mag_primary": None if m1 < 0 else m1,
                "mag_secondary": None if m2 < 0 else m2,
                "observer": self.w_observer.text().strip()
                or self.creds.get_network("wds").get("observer")
                or None,
                "observatory": self.w_observatory.text().strip() or None,
            }
            out = self.artifacts_root / "export" / "wds" / f"{pid}.txt"
            try:
                ExportWds(self.archive).execute(
                    product_id=pid,
                    out_path=out,
                    overrides=overrides,
                )
                store = LocalArtifactStore(self.artifacts_root)
                uri = store.put(out, key=f"export/wds/{out.name}")
                csv_path = out.with_suffix(".csv")
                if csv_path.is_file():
                    store.put(csv_path, key=f"export/wds/{csv_path.name}")
                sub = NetworkSubmission(
                    id=new_id(),
                    workspace_id=self._workspace_id,
                    network="wds",
                    status="validated",
                    artifact_uri=uri,
                    product_id=pid,
                    payload_summary={
                        "object": obj,
                        "note": "submit manual USNO / WDS",
                    },
                )
                self.archive.save_network_submission(sub)
                self._log(
                    f"WDS wrote {out} - submit https://www.astro.gsu.edu/wds/"
                )
                self.refresh()
            except Exception as exc:  # noqa: BLE001
                QMessageBox.critical(self, "WDS", str(exc))

        def _run_cobs(self) -> None:
            if self._workspace_id is None:
                QMessageBox.warning(self, "Contribute", "Sem workspace.")
                return
            product_id = _parse_uuid(self.c_product.text())
            if product_id is not None:
                filled = prefill_cobs_fields(
                    self.archive,
                    credentials=self.creds.get_network("cobs"),
                    current=self._cobs_current(),
                )
                self._apply_cobs_fields(filled)
            mag_val = float(self.c_mag.value())
            mag = None if mag_val < -5 else mag_val
            ap = float(self.c_aperture.value())
            overrides: dict[str, Any] = {
                "designation": self.c_desig.text().strip() or None,
                "epoch_utc": self.c_epoch.text().strip() or None,
                "mag": mag,
                "mag_method": self.c_method.text().strip() or "B",
                "aperture_cm": None if ap <= 0 else ap,
                "obscode": self.c_obscode.text().strip()
                or self.creds.get_network("cobs").get("obscode")
                or None,
                "observer": self.c_observer.text().strip()
                or self.creds.get_network("cobs").get("observer")
                or None,
                "location": self.c_location.text().strip() or None,
            }
            check = validate_product_for_network(
                self.archive,
                network="cobs",
                product_id=product_id,
                payload=overrides,
            )
            if not check.ok:
                QMessageBox.warning(
                    self,
                    "Validacao COBS",
                    "\n".join(check.error_messages()) or "Campos incompletos.",
                )
                return
            out_name = f"{product_id}.txt" if product_id else "gui_cobs.txt"
            out = self.artifacts_root / "export" / "cobs" / out_name
            try:
                ExportCobs(self.archive).execute(
                    product_id=product_id,
                    out_path=out,
                    overrides=overrides,
                )
                store = LocalArtifactStore(self.artifacts_root)
                uri = store.put(out, key=f"export/cobs/{out.name}")
                csv_path = out.with_suffix(".csv")
                if csv_path.is_file():
                    store.put(csv_path, key=f"export/cobs/{csv_path.name}")
                sub = NetworkSubmission(
                    id=new_id(),
                    workspace_id=self._workspace_id,
                    network="cobs",
                    status="validated",
                    artifact_uri=uri,
                    product_id=product_id,
                    payload_summary={
                        "designation": self.c_desig.text().strip(),
                        "note": "submit manual https://www.cobs.si/",
                    },
                )
                self.archive.save_network_submission(sub)
                self._log(f"COBS wrote {out} - submit https://www.cobs.si/")
                self.refresh()
            except Exception as exc:  # noqa: BLE001
                QMessageBox.critical(self, "COBS", str(exc))

        def _run_tns(self) -> None:
            if self._workspace_id is None:
                QMessageBox.warning(self, "Contribute", "Sem workspace.")
                return
            tcred = self.creds.get_network("tns")
            if self.t_product.text().strip():
                filled = prefill_tns_fields(
                    self.archive,
                    credentials=tcred,
                    current=self._tns_current(),
                )
                self._apply_tns_fields(filled)
            try:
                groupid = int(self.t_group.text().strip() or tcred.get("groupid") or 0)
            except ValueError:
                QMessageBox.warning(self, "TNS", "groupid invalido.")
                return
            check = validate_product_for_network(
                self.archive,
                network="tns",
                product_id=_parse_uuid(self.t_product.text()),
                payload={
                    "ra_deg": float(self.t_ra.value()),
                    "dec_deg": float(self.t_dec.value()),
                },
            )
            if not check.ok:
                QMessageBox.warning(
                    self,
                    "Validacao TNS",
                    "\n".join(check.error_messages()) or "Campos incompletos.",
                )
                return
            report = format_tns_at_report(
                ra_deg=float(self.t_ra.value()),
                dec_deg=float(self.t_dec.value()),
                groupid=groupid,
                reporter="AstroCitizen",
                discovery_mag=float(self.t_mag.value()),
            )
            out = self.artifacts_root / "export" / "tns" / "at.json"
            try:
                write_tns_report(out, report)
                do_submit = bool(self.t_submit.currentData())
                api_key = str(tcred.get("api_key") or "dry-run-key")
                user_id = str(tcred.get("user_id") or "0")
                if do_submit and (api_key == "dry-run-key" or user_id == "0"):
                    QMessageBox.warning(
                        self,
                        "TNS",
                        "Submit requer credentials tns.api_key e user_id.",
                    )
                    return
                meta = TnsClient(
                    api_key=api_key, user_id=user_id, sandbox=True
                ).submit_report(report, dry_run=not do_submit)
                store = LocalArtifactStore(self.artifacts_root)
                uri = store.put(out, key=f"export/tns/{out.name}")
                sub = NetworkSubmission(
                    id=new_id(),
                    workspace_id=self._workspace_id,
                    network="tns",
                    status=str(meta.get("status") or "draft"),
                    artifact_uri=uri,
                    payload_summary={"meta": meta},
                    remote_ack=str(meta.get("response") or "")[:500] or None,
                )
                self.archive.save_network_submission(sub)
                self._log(f"TNS {sub.status} {out}")
                self.refresh()
            except Exception as exc:  # noqa: BLE001
                QMessageBox.critical(self, "TNS", str(exc))

        def _run_bess(self) -> None:
            if self._workspace_id is None:
                QMessageBox.warning(self, "Contribute", "Sem workspace.")
                return
            import numpy as np

            if self.b_product.text().strip():
                filled = prefill_bess_fields(
                    self.archive,
                    credentials=self.creds.get_network("bess"),
                    current=self._bess_current(),
                )
                self._apply_bess_fields(filled)
            observer = (
                self.b_obs.text().strip()
                or self.creds.get_network("bess").get("observer")
                or "AstroCitizen"
            )
            check = validate_product_for_network(
                self.archive,
                network="bess",
                product_id=_parse_uuid(self.b_product.text()),
                payload={
                    "observer": observer,
                    "objname": self.b_obj.text().strip(),
                    "date_obs": self.b_date.text().strip(),
                },
            )
            if not check.ok:
                QMessageBox.warning(
                    self,
                    "Validacao BeSS",
                    "\n".join(check.error_messages()) or "Campos incompletos.",
                )
                return
            out = self.artifacts_root / "export" / "bess" / "gui_bess.fits"
            try:
                wave = np.linspace(400.0, 700.0, 301)
                write_bess_fits(
                    out,
                    objname=self.b_obj.text().strip() or "BeStar",
                    observer=str(observer),
                    date_obs=self.b_date.text().strip() or "2026-07-21T01:00:00",
                    exptime_s=60.0,
                    wavelength_nm=wave,
                    flux=np.ones_like(wave),
                )
                store = LocalArtifactStore(self.artifacts_root)
                uri = store.put(out, key=f"export/bess/{out.name}")
                sub = NetworkSubmission(
                    id=new_id(),
                    workspace_id=self._workspace_id,
                    network="bess",
                    status="draft",
                    artifact_uri=uri,
                    product_id=_parse_uuid(self.b_product.text()),
                    payload_summary={"note": "upload BeSS portal"},
                )
                self.archive.save_network_submission(sub)
                self._log(f"BeSS wrote {out} - http://basebe.obspm.fr/")
                self.refresh()
            except Exception as exc:  # noqa: BLE001
                QMessageBox.critical(self, "BeSS", str(exc))

        def _run_exoclock(self) -> None:
            if self._workspace_id is None:
                QMessageBox.warning(self, "Contribute", "Sem workspace.")
                return
            try:
                pid = UUID(self.e_product.text().strip())
            except ValueError:
                QMessageBox.warning(self, "ExoClock", "Product UUID invalido.")
                return
            filled = prefill_exoclock_fields(
                self.archive,
                credentials=self.creds.get_network("exoclock"),
                current=self._exoclock_current(),
            )
            self._apply_exoclock_fields(filled)
            target = self.e_target.text().strip() or "TARGET"
            check = validate_product_for_network(
                self.archive,
                network="exoclock",
                product_id=pid,
                payload={"target": target},
            )
            if not check.ok:
                QMessageBox.warning(
                    self,
                    "Validacao ExoClock",
                    "\n".join(check.error_messages()) or "Produto incompleto.",
                )
                return
            observer = self.creds.get_network("exoclock").get("observer") or "AstroCitizen"
            out = self.artifacts_root / "export" / "exoclock" / f"{pid}.txt"
            try:
                ExportExoclock(self.archive).execute(
                    product_id=pid,
                    target=target,
                    out_path=out,
                    observer=str(observer),
                )
                store = LocalArtifactStore(self.artifacts_root)
                uri = store.put(out, key=f"export/exoclock/{out.name}")
                sub = NetworkSubmission(
                    id=new_id(),
                    workspace_id=self._workspace_id,
                    network="exoclock",
                    status="draft",
                    artifact_uri=uri,
                    product_id=pid,
                    payload_summary={"target": target},
                )
                self.archive.save_network_submission(sub)
                self._log(f"ExoClock wrote {out} - https://www.exoclock.space/upload/")
                self.refresh()
            except Exception as exc:  # noqa: BLE001
                QMessageBox.critical(self, "ExoClock", str(exc))

        def _run_iota(self) -> None:
            import shutil

            if self._workspace_id is None:
                QMessageBox.warning(self, "Contribute", "Sem workspace.")
                return
            if self.i_product.text().strip():
                filled = prefill_iota_fields(
                    self.archive,
                    credentials=self.creds.get_network("iota"),
                    current=self._iota_current(),
                )
                self._apply_iota_fields(filled)
            observer = (
                self.i_obs.text().strip()
                or self.creds.get_network("iota").get("observer")
                or "AstroCitizen"
            )
            check = validate_product_for_network(
                self.archive,
                network="iota",
                product_id=_parse_uuid(self.i_product.text()),
                payload={
                    "event_id": self.i_event.text().strip(),
                    "star": self.i_star.text().strip(),
                    "asteroid": self.i_ast.text().strip(),
                    "observer": observer,
                },
            )
            if not check.ok:
                QMessageBox.warning(
                    self,
                    "Validacao IOTA",
                    "\n".join(check.error_messages()) or "Campos incompletos.",
                )
                return
            if not self.i_event.text().strip():
                QMessageBox.warning(self, "IOTA", "Event ID obrigatorio.")
                return
            sites = self.archive.list_sites(self._workspace_id)
            if not sites:
                QMessageBox.warning(self, "IOTA", "Sem sites no workspace.")
                return
            site = sites[0]
            pack = self.artifacts_root / "export" / "iota" / "gui_pack"
            try:
                write_iota_pack(
                    pack,
                    event_id=self.i_event.text().strip(),
                    star=self.i_star.text().strip() or "star",
                    asteroid=self.i_ast.text().strip() or "asteroid",
                    observer=str(observer),
                    latitude_deg=site.latitude_deg,
                    longitude_deg=site.longitude_deg,
                    elevation_m=site.elevation_m,
                    result=self.i_result.currentText(),
                )
                zip_path = Path(shutil.make_archive(str(pack), "zip", root_dir=pack))
                store = LocalArtifactStore(self.artifacts_root)
                uri = store.put(zip_path, key=f"export/iota/{zip_path.name}")
                sub = NetworkSubmission(
                    id=new_id(),
                    workspace_id=self._workspace_id,
                    network="iota",
                    status="draft",
                    artifact_uri=uri,
                    product_id=_parse_uuid(self.i_product.text()),
                    payload_summary={"event": self.i_event.text()},
                )
                self.archive.save_network_submission(sub)
                self._log(f"IOTA pack {zip_path}")
                self.refresh()
            except Exception as exc:  # noqa: BLE001
                QMessageBox.critical(self, "IOTA", str(exc))

    return ContributeDashboard
