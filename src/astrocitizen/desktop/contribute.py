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
    for net in ("aavso", "mpc", "tns", "bess", "exoclock", "iota", "wds"):
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
        if net in ("bess", "exoclock", "iota", "wds") and vals.get("observer"):
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
    for key in ("star", "star_name", "target_name", "target", "object"):
        val = params.get(key) or summary.get(key)
        if val and str(val).strip().upper() not in ("", "UNKNOWN", "TARGET"):
            return str(val).strip()
    tid = params.get("target_id") or summary.get("target_id")
    uid = _parse_uuid(tid)
    if uid is not None and hasattr(archive, "get_target"):
        target = archive.get_target(uid)
        if target is not None:
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
    from astrocitizen.shared.ids import new_id
    from astrocitizen.shared.paths import default_artifacts_root

    class FieldReviewDialog(QDialog):
        """Revisar campos atlas antes de export (AAVSO / MPC / WDS)."""

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
            if self.network == "aavso":
                filled = prefill_aavso_fields(
                    self.archive, credentials={}, current=vals
                )
            elif self.network == "wds":
                filled = prefill_wds_fields(
                    self.archive, credentials={}, current=vals
                )
            else:
                filled = prefill_mpc_fields(
                    self.archive, credentials={}, current=vals
                )
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
            for n in ("aavso", "mpc", "tns", "bess", "exoclock", "iota", "wds"):
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
            review = QPushButton("Revisar campos")
            review.clicked.connect(lambda: self._review_fields("aavso"))
            btn = QPushButton("Export Extended (WebObs)")
            btn.clicked.connect(self._run_aavso)
            form.addRow("Product UUID", self.a_product)
            form.addRow("Star", self.a_star)
            form.addRow("OBSCODE", self.a_obscode)
            form.addRow("Band", self.a_band)
            form.addRow("Chart", self.a_chart)
            row = QHBoxLayout()
            row.addWidget(review)
            row.addWidget(btn)
            form.addRow(row)
            return w

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

        def _tab_tns(self) -> QWidget:
            w = QWidget()
            form = QFormLayout(w)
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
            btn = QPushButton("TNS AT-rep")
            btn.clicked.connect(self._run_tns)
            form.addRow("RA deg", self.t_ra)
            form.addRow("Dec deg", self.t_dec)
            form.addRow("Mag", self.t_mag)
            form.addRow("Group id", self.t_group)
            form.addRow("Modo", self.t_submit)
            form.addRow(btn)
            return w

        def _tab_bess(self) -> QWidget:
            w = QWidget()
            form = QFormLayout(w)
            self.b_obj = QLineEdit()
            self.b_obj.setText("gam Cas")
            self.b_obs = QLineEdit()
            self.b_date = QLineEdit()
            self.b_date.setText("2026-07-21T01:00:00")
            btn = QPushButton("Gerar FITS 1D BeSS")
            btn.clicked.connect(self._run_bess)
            form.addRow("OBJNAME", self.b_obj)
            form.addRow("Observer", self.b_obs)
            form.addRow("DATE-OBS", self.b_date)
            form.addRow(btn)
            return w

        def _tab_exoclock(self) -> QWidget:
            w = QWidget()
            form = QFormLayout(w)
            self.e_product = QLineEdit()
            self.e_target = QLineEdit()
            self.e_target.setText("WASP-12b")
            btn = QPushButton("Export LC ExoClock")
            btn.clicked.connect(self._run_exoclock)
            form.addRow("Product UUID", self.e_product)
            form.addRow("Target", self.e_target)
            form.addRow(btn)
            return w

        def _tab_iota(self) -> QWidget:
            w = QWidget()
            form = QFormLayout(w)
            self.i_event = QLineEdit()
            self.i_star = QLineEdit()
            self.i_ast = QLineEdit()
            self.i_obs = QLineEdit()
            self.i_result = QComboBox()
            self.i_result.addItems(["positive", "negative"])
            btn = QPushButton("Pacote IOTA-ES")
            btn.clicked.connect(self._run_iota)
            form.addRow("Event ID", self.i_event)
            form.addRow("Star", self.i_star)
            form.addRow("Asteroid", self.i_ast)
            form.addRow("Observer", self.i_obs)
            form.addRow("Result", self.i_result)
            form.addRow(btn)
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
            t_cred = self.creds.get_network("tns")
            if t_cred.get("groupid") is not None and self.t_group.text() == "0":
                self.t_group.setText(str(t_cred["groupid"]))
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
                    "e_product",
                    "b_product",
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
            if network == "aavso":
                initial = prefill_aavso_fields(
                    self.archive,
                    credentials=self.creds.get_network("aavso"),
                    current=self._aavso_current(),
                )
            elif network == "wds":
                initial = prefill_wds_fields(
                    self.archive,
                    credentials=self.creds.get_network("wds"),
                    current=self._wds_current(),
                )
            else:
                initial = prefill_mpc_fields(
                    self.archive,
                    credentials=self.creds.get_network("mpc"),
                    current=self._mpc_current(),
                )
            dlg = FieldReviewDialog(
                self, network=network, archive=self.archive, initial=initial
            )
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
            vals = dlg.values()
            if network == "aavso":
                self._apply_aavso_fields(vals)
            elif network == "wds":
                self._apply_wds_fields(vals)
            else:
                self._apply_mpc_fields(vals)
            self._save_review_draft(
                network=network,
                vals=vals,
                product_id=_parse_uuid(vals.get("product_id")),
            )

        def _run_aavso(self) -> None:
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
            check = validate_product_for_network(
                self.archive,
                network="aavso",
                product_id=pid,
                payload={"obscode": obscode, "star": star},
            )
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
                    chart=self.a_chart.text().strip() or "NA",
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
                        "chart": self.a_chart.text().strip() or "NA",
                        "note": "WebObs manual",
                    },
                )
                self.archive.save_network_submission(sub)
                self._log(f"AAVSO wrote {out} - upload https://www.aavso.org/webobs/")
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

        def _run_tns(self) -> None:
            if self._workspace_id is None:
                QMessageBox.warning(self, "Contribute", "Sem workspace.")
                return
            tcred = self.creds.get_network("tns")
            try:
                groupid = int(self.t_group.text().strip() or tcred.get("groupid") or 0)
            except ValueError:
                QMessageBox.warning(self, "TNS", "groupid invalido.")
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

            observer = (
                self.b_obs.text().strip()
                or self.creds.get_network("bess").get("observer")
                or "AstroCitizen"
            )
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
            observer = self.creds.get_network("exoclock").get("observer") or "AstroCitizen"
            out = self.artifacts_root / "export" / "exoclock" / f"{pid}.txt"
            try:
                ExportExoclock(self.archive).execute(
                    product_id=pid,
                    target=self.e_target.text().strip() or "TARGET",
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
                    payload_summary={"target": self.e_target.text()},
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
            if not self.i_event.text().strip():
                QMessageBox.warning(self, "IOTA", "Event ID obrigatorio.")
                return
            sites = self.archive.list_sites(self._workspace_id)
            if not sites:
                QMessageBox.warning(self, "IOTA", "Sem sites no workspace.")
                return
            site = sites[0]
            observer = (
                self.i_obs.text().strip()
                or self.creds.get_network("iota").get("observer")
                or "AstroCitizen"
            )
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
                    payload_summary={"event": self.i_event.text()},
                )
                self.archive.save_network_submission(sub)
                self._log(f"IOTA pack {zip_path}")
                self.refresh()
            except Exception as exc:  # noqa: BLE001
                QMessageBox.critical(self, "IOTA", str(exc))

    return ContributeDashboard
