"""Painel Contribute: envios AAVSO / MPC / TNS (AC-143)."""

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
    for net in ("aavso", "mpc", "tns", "bess", "exoclock", "iota"):
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
        if net in ("bess", "exoclock", "iota") and vals.get("observer"):
            keys.append(f"observer={vals['observer']}")
        lines.append(f"{net}: {', '.join(keys) if keys else '(vazio)'}")
    return lines


def build_contribute_dashboard(parent: Any | None = None) -> Any:
    """Devolve ContributeDashboard (requer PySide6)."""
    from PySide6.QtWidgets import (
        QComboBox,
        QDoubleSpinBox,
        QFormLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
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
    from astrocitizen.shared.ids import new_id
    from astrocitizen.shared.paths import default_artifacts_root

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
            for n in ("aavso", "mpc", "tns", "bess", "exoclock", "iota"):
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
            btn = QPushButton("Export Extended (WebObs)")
            btn.clicked.connect(self._run_aavso)
            form.addRow("Product UUID", self.a_product)
            form.addRow("Star", self.a_star)
            form.addRow("OBSCODE", self.a_obscode)
            form.addRow("Band", self.a_band)
            form.addRow(btn)
            return w

        def _tab_mpc(self) -> QWidget:
            w = QWidget()
            form = QFormLayout(w)
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
            self.m_email = QLineEdit()
            self.m_submit = QComboBox()
            self.m_submit.addItem("Dry-run", False)
            self.m_submit.addItem("Submit real", True)
            btn = QPushButton("ADES PSV")
            btn.clicked.connect(self._run_mpc)
            form.addRow("Designation", self.m_desig)
            form.addRow("Obs code", self.m_code)
            form.addRow("Epoch UTC", self.m_epoch)
            form.addRow("RA deg", self.m_ra)
            form.addRow("Dec deg", self.m_dec)
            form.addRow("Email", self.m_email)
            form.addRow("Modo", self.m_submit)
            form.addRow(btn)
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

        def focus_network(self, network: str | None) -> None:
            """Filtra lista e abre tab de export da rede (ex.: aavso)."""
            if network:
                key = str(network).lower()
                i = self.filter_combo.findData(key)
                if i >= 0:
                    self.filter_combo.setCurrentIndex(i)
                titles = {
                    "aavso": "AAVSO",
                    "mpc": "MPC",
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
            self.refresh()

        def _log(self, msg: str) -> None:
            self.log.append(msg)

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
            out = self.artifacts_root / "export" / "aavso" / f"{pid}.txt"
            try:
                ExportAavso(self.archive).execute(
                    product_id=pid,
                    star_name=star,
                    observer_code=str(obscode),
                    out_path=out,
                    band=self.a_band.text().strip() or "V",
                )
                store = LocalArtifactStore(self.artifacts_root)
                uri = store.put(out, key=f"export/aavso/{out.name}")
                sub = NetworkSubmission(
                    id=new_id(),
                    workspace_id=self._workspace_id,
                    network="aavso",
                    status="draft",
                    artifact_uri=uri,
                    product_id=pid,
                    payload_summary={"star": star, "note": "WebObs manual"},
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
            out = self.artifacts_root / "export" / "mpc" / "gui.psv"
            try:
                write_ades_psv(
                    out,
                    observatory_code=str(code),
                    designation=self.m_desig.text().strip(),
                    observations=[
                        {
                            "epoch_utc": self.m_epoch.text().strip(),
                            "ra_deg": float(self.m_ra.value()),
                            "dec_deg": float(self.m_dec.value()),
                        }
                    ],
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
                    payload_summary={"designation": self.m_desig.text(), "meta": meta},
                    remote_ack=str(meta.get("response") or meta.get("ack") or "")[:500]
                    or None,
                )
                self.archive.save_network_submission(sub)
                self._log(f"MPC {sub.status} {out}")
                self.refresh()
            except Exception as exc:  # noqa: BLE001
                QMessageBox.critical(self, "MPC", str(exc))

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
