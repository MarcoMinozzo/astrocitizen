"""Painel Timing: IOTA previsao + contactos + video/LC (PO-D01 / ENTRADA #5)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID


def build_timing_dashboard() -> type:
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QFileDialog,
        QFormLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMessageBox,
        QPushButton,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    from astrocitizen.adapters.fs import LocalArtifactStore
    from astrocitizen.contribution.iota import write_iota_pack
    from astrocitizen.observatory import (
        ImportIotaPrediction,
        RegisterOccultationTiming,
    )
    from astrocitizen.shared.errors import DomainError
    from astrocitizen.shared.paths import default_artifacts_root

    class TimingDashboard(QWidget):
        def __init__(
            self,
            archive: Any,
            *,
            artifacts_root: Path | None = None,
            on_changed: Any | None = None,
        ) -> None:
            super().__init__()
            self.archive = archive
            self.artifacts_root = Path(artifacts_root or default_artifacts_root())
            self.on_changed = on_changed
            self._pred_id: UUID | None = None
            self._timing_id: UUID | None = None

            root = QVBoxLayout(self)
            root.setContentsMargins(16, 12, 16, 12)
            title = QLabel("Timing — IOTA ocultacao (PO-D01)")
            title.setObjectName("pageTitle")
            root.addWidget(title)

            hint = QLabel(
                "1) Importar previsao  2) Anexar video/SER e/ou LC CSV  "
                "3) Registar contactos D/R (GPS/NTP/VTI)  4) Exportar pacote IOTA-ES."
            )
            hint.setObjectName("emptyState")
            hint.setWordWrap(True)
            root.addWidget(hint)

            form = QFormLayout()
            self.pred_path = QLineEdit()
            browse = QPushButton("Ficheiro...")
            browse.setObjectName("secondaryBtn")
            browse.clicked.connect(self._browse_pred)
            prow = QHBoxLayout()
            prow.addWidget(self.pred_path, 1)
            prow.addWidget(browse)
            pwrap = QWidget()
            pwrap.setLayout(prow)
            form.addRow("Previsao", pwrap)

            self.site = QComboBox()
            self.program = QComboBox()
            form.addRow("Site", self.site)
            form.addRow("Programa", self.program)

            btn_imp = QPushButton("Importar previsao")
            btn_imp.clicked.connect(self._import_pred)
            form.addRow(btn_imp)

            self.event_id = QLineEdit()
            self.star = QLineEdit()
            self.asteroid = QLineEdit()
            self.result = QComboBox()
            self.result.addItem("positive", "positive")
            self.result.addItem("negative", "negative")
            self.result.addItem("missed", "missed")
            self.d_time = QLineEdit()
            self.d_time.setPlaceholderText("UTC ISO D (desaparecimento)")
            self.r_time = QLineEdit()
            self.r_time.setPlaceholderText("UTC ISO R (reaparecimento)")
            self.timesource = QComboBox()
            for ts in ("NTP", "GPS", "VTI", "manual", "PC"):
                self.timesource.addItem(ts, ts)
            self.observer = QLineEdit("AstroCitizen")
            self.notes = QLineEdit()
            form.addRow("EventID", self.event_id)
            form.addRow("Star", self.star)
            form.addRow("Asteroid", self.asteroid)
            form.addRow("Result", self.result)
            form.addRow("D_time UTC", self.d_time)
            form.addRow("R_time UTC", self.r_time)
            form.addRow("TimeSource", self.timesource)
            form.addRow("Observer", self.observer)
            form.addRow("Notes", self.notes)

            self.video_path = QLineEdit()
            vbrowse = QPushButton("Video...")
            vbrowse.setObjectName("secondaryBtn")
            vbrowse.clicked.connect(self._browse_video)
            vrow = QHBoxLayout()
            vrow.addWidget(self.video_path, 1)
            vrow.addWidget(vbrowse)
            vwrap = QWidget()
            vwrap.setLayout(vrow)
            form.addRow("Video/SER", vwrap)

            self.lc_path = QLineEdit()
            lbrowse = QPushButton("LC CSV...")
            lbrowse.setObjectName("secondaryBtn")
            lbrowse.clicked.connect(self._browse_lc)
            lrow = QHBoxLayout()
            lrow.addWidget(self.lc_path, 1)
            lrow.addWidget(lbrowse)
            lwrap = QWidget()
            lwrap.setLayout(lrow)
            form.addRow("Curva luz", lwrap)

            self.suggest = QCheckBox("Sugerir D/R a partir do LC")
            form.addRow(self.suggest)

            bar = QHBoxLayout()
            btn_reg = QPushButton("Registar timing")
            btn_reg.clicked.connect(self._register)
            btn_exp = QPushButton("Exportar pacote IOTA")
            btn_exp.setObjectName("secondaryBtn")
            btn_exp.clicked.connect(self._export_pack)
            bar.addWidget(btn_reg)
            bar.addWidget(btn_exp)
            bar.addStretch(1)
            form.addRow(bar)
            root.addLayout(form)

            self.log = QTextEdit()
            self.log.setReadOnly(True)
            root.addWidget(self.log, 1)

        def _append(self, msg: str) -> None:
            self.log.append(msg)

        def _workspace(self):
            ws = self.archive.list_workspaces()
            return ws[0] if ws else None

        def reload(self) -> None:
            ws = self._workspace()
            if ws is None:
                return
            sites = self.archive.list_sites(ws.id)
            progs = self.archive.list_programs(ws.id)
            cur_s, cur_p = self.site.currentData(), self.program.currentData()
            self.site.clear()
            self.site.addItem("(nenhum)", None)
            for s in sites:
                self.site.addItem(s.name, s.id)
            self.program.clear()
            self.program.addItem("(nenhum)", None)
            for p in progs:
                self.program.addItem(f"{p.template_id} · {p.name}", p.id)
            if cur_s is not None:
                i = self.site.findData(cur_s)
                if i >= 0:
                    self.site.setCurrentIndex(i)
            if cur_p is not None:
                i = self.program.findData(cur_p)
                if i >= 0:
                    self.program.setCurrentIndex(i)

        def _browse_pred(self) -> None:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Previsao IOTA",
                "",
                "Pred (*.txt *.csv);;All (*)",
            )
            if path:
                self.pred_path.setText(path)

        def _browse_video(self) -> None:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Video ocultacao",
                "",
                "Video (*.ser *.avi *.mp4 *.mov *.mkv);;All (*)",
            )
            if path:
                self.video_path.setText(path)

        def _browse_lc(self) -> None:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Curva de luz",
                "",
                "CSV (*.csv *.txt);;All (*)",
            )
            if path:
                self.lc_path.setText(path)

        def _import_pred(self) -> None:
            ws = self._workspace()
            if ws is None:
                return
            path = Path(self.pred_path.text().strip())
            if not path.is_file():
                QMessageBox.warning(self, "Timing", "Ficheiro de previsao invalido.")
                return
            store = LocalArtifactStore(self.artifacts_root)
            try:
                product = ImportIotaPrediction(self.archive, store).execute(
                    workspace_id=ws.id,
                    path=path,
                    program_id=self.program.currentData(),
                    site_id=self.site.currentData(),
                )
            except DomainError as exc:
                QMessageBox.critical(self, "Timing", str(exc))
                return
            self._pred_id = product.id
            p = product.parameters
            self.event_id.setText(str(p.get("event_id") or ""))
            self.star.setText(str(p.get("star") or ""))
            self.asteroid.setText(str(p.get("asteroid") or ""))
            if p.get("event_utc"):
                self.d_time.setText(str(p["event_utc"]))
            self._append(
                f"prediction={product.id}  event={p.get('event_id')}  "
                f"star={p.get('star')}  asteroid={p.get('asteroid')}"
            )
            if self.on_changed:
                self.on_changed()

        def _register(self) -> None:
            ws = self._workspace()
            if ws is None:
                return
            store = LocalArtifactStore(self.artifacts_root)
            vtxt = self.video_path.text().strip()
            ltxt = self.lc_path.text().strip()
            try:
                product = RegisterOccultationTiming(self.archive, store).execute(
                    workspace_id=ws.id,
                    event_id=self.event_id.text(),
                    star=self.star.text(),
                    asteroid=self.asteroid.text(),
                    result=str(self.result.currentData()),
                    d_time_utc=self.d_time.text().strip() or None,
                    r_time_utc=self.r_time.text().strip() or None,
                    timesource=str(self.timesource.currentData() or "NTP"),
                    site_id=self.site.currentData(),
                    program_id=self.program.currentData(),
                    prediction_product_id=self._pred_id,
                    observer=self.observer.text().strip() or "AstroCitizen",
                    notes=self.notes.text().strip(),
                    video_path=Path(vtxt) if vtxt else None,
                    lc_csv_path=Path(ltxt) if ltxt else None,
                    suggest_contacts=self.suggest.isChecked(),
                )
            except DomainError as exc:
                QMessageBox.critical(self, "Timing", str(exc))
                return
            self._timing_id = product.id
            if product.summary.get("d_time_utc"):
                self.d_time.setText(str(product.summary["d_time_utc"]))
            if product.summary.get("r_time_utc"):
                self.r_time.setText(str(product.summary["r_time_utc"]))
            self._append(
                f"timing={product.id}  result={product.summary.get('result')}  "
                f"D={product.summary.get('d_time_utc')}  "
                f"R={product.summary.get('r_time_utc')}  "
                f"video={product.summary.get('has_video')}  "
                f"lc_n={product.summary.get('n_lc_points')}"
            )
            if self.on_changed:
                self.on_changed()

        def _export_pack(self) -> None:
            ws = self._workspace()
            if ws is None:
                return
            sid = self.site.currentData()
            site = self.archive.get_site(sid) if sid else None
            lat = site.latitude_deg if site else 0.0
            lon = site.longitude_deg if site else 0.0
            elev = site.elevation_m if site else 0.0
            pack = self.artifacts_root / "export" / "iota" / "timing_pack"
            try:
                write_iota_pack(
                    pack,
                    event_id=self.event_id.text().strip() or "unknown",
                    star=self.star.text().strip() or "unknown",
                    asteroid=self.asteroid.text().strip() or "unknown",
                    observer=self.observer.text().strip() or "AstroCitizen",
                    latitude_deg=lat,
                    longitude_deg=lon,
                    elevation_m=elev,
                    result=str(self.result.currentData()),
                    d_time_utc=self.d_time.text().strip() or None,
                    r_time_utc=self.r_time.text().strip() or None,
                    timesource=str(self.timesource.currentData() or "NTP"),
                    notes=self.notes.text().strip(),
                )
            except Exception as exc:
                QMessageBox.critical(self, "Timing", str(exc))
                return
            self._append(f"pack -> {pack}")
            QMessageBox.information(self, "Timing", f"Pacote IOTA escrito:\n{pack}")

    return TimingDashboard
