"""Painel Observar: Solar (PO-E03) + Log visual (PO-F03)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID


def build_observe_dashboard() -> type:
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QDoubleSpinBox,
        QFileDialog,
        QFormLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMessageBox,
        QPushButton,
        QSpinBox,
        QTabWidget,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    from astrocitizen.adapters.fs import LocalArtifactStore
    from astrocitizen.analysis import CountSunspots
    from astrocitizen.contribution.solar import ExportSolarReport
    from astrocitizen.observatory import LogVisualObservation
    from astrocitizen.shared.errors import DomainError
    from astrocitizen.shared.paths import default_artifacts_root

    class ObserveDashboard(QWidget):
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
            self._last_solar_id: UUID | None = None

            root = QVBoxLayout(self)
            root.setContentsMargins(16, 12, 16, 12)
            title = QLabel("Observar — Solar / Visual")
            title.setObjectName("pageTitle")
            root.addWidget(title)

            warn = QLabel(
                "SOL: nunca observe sem filtro certificado. "
                "Checklist obrigatorio antes de contar manchas."
            )
            warn.setObjectName("emptyState")
            warn.setWordWrap(True)
            root.addWidget(warn)

            self.tabs = QTabWidget()
            self.tabs.addTab(self._tab_solar(), "Solar (PO-E03)")
            self.tabs.addTab(self._tab_visual(), "Log visual (PO-F03)")
            root.addWidget(self.tabs)

            self.log = QTextEdit()
            self.log.setReadOnly(True)
            self.log.setMaximumHeight(140)
            root.addWidget(self.log)

        def _workspace(self):
            ws = self.archive.list_workspaces()
            return ws[0] if ws else None

        def _append(self, msg: str) -> None:
            self.log.append(msg)

        def reload(self) -> None:
            ws = self._workspace()
            if ws is None:
                return
            sites = self.archive.list_sites(ws.id)
            progs = self.archive.list_programs(ws.id)
            targets = self.archive.list_targets(ws.id)

            def refill(combo: QComboBox, items: list, label_fn, optional: bool = True) -> None:
                cur = combo.currentData()
                combo.clear()
                if optional:
                    combo.addItem("(nenhum)", None)
                for it in items:
                    combo.addItem(label_fn(it), it.id)
                if cur is not None:
                    i = combo.findData(cur)
                    if i >= 0:
                        combo.setCurrentIndex(i)

            refill(self.s_site, sites, lambda s: s.name)
            refill(self.s_prog, progs, lambda p: f"{p.template_id} · {p.name}")
            refill(self.v_site, sites, lambda s: s.name)
            refill(self.v_prog, progs, lambda p: f"{p.template_id} · {p.name}")
            refill(self.v_target, targets, lambda t: t.designation)

        def _tab_solar(self) -> QWidget:
            w = QWidget()
            form = QFormLayout(w)
            self.s_path = QLineEdit()
            self.s_path.setPlaceholderText("FITS luz branca...")
            browse = QPushButton("Ficheiro...")
            browse.setObjectName("secondaryBtn")
            browse.clicked.connect(self._browse_fits)
            row = QHBoxLayout()
            row.addWidget(self.s_path, 1)
            row.addWidget(browse)
            wrap = QWidget()
            wrap.setLayout(row)
            form.addRow("FITS", wrap)

            self.s_filter_ok = QCheckBox("Filtro solar certificado confirmado")
            self.s_no_eyepiece = QCheckBox("Sem ocular sem filtro")
            self.s_daytime = QCheckBox("Observacao diurna consciente")
            form.addRow(self.s_filter_ok)
            form.addRow(self.s_no_eyepiece)
            form.addRow(self.s_daytime)

            self.s_filter_name = QLineEdit("white-light")
            self.s_observer = QLineEdit("AstroCitizen")
            self.s_k = QDoubleSpinBox()
            self.s_k.setRange(0.1, 5.0)
            self.s_k.setDecimals(2)
            self.s_k.setValue(1.0)
            self.s_spots = QSpinBox()
            self.s_spots.setRange(-1, 500)
            self.s_spots.setSpecialValueText("auto")
            self.s_spots.setValue(-1)
            self.s_groups = QSpinBox()
            self.s_groups.setRange(-1, 100)
            self.s_groups.setSpecialValueText("auto")
            self.s_groups.setValue(-1)
            self.s_site = QComboBox()
            self.s_prog = QComboBox()
            form.addRow("Filtro", self.s_filter_name)
            form.addRow("Observador", self.s_observer)
            form.addRow("k (Wolf)", self.s_k)
            form.addRow("Spots (manual)", self.s_spots)
            form.addRow("Groups (manual)", self.s_groups)
            form.addRow("Site", self.s_site)
            form.addRow("Programa", self.s_prog)

            btn_run = QPushButton("Contar manchas")
            btn_run.clicked.connect(self._run_solar)
            btn_export = QPushButton("Exportar ultimo relatorio")
            btn_export.setObjectName("secondaryBtn")
            btn_export.clicked.connect(self._export_solar)
            bar = QHBoxLayout()
            bar.addWidget(btn_run)
            bar.addWidget(btn_export)
            bar.addStretch(1)
            form.addRow(bar)
            return w

        def _tab_visual(self) -> QWidget:
            w = QWidget()
            form = QFormLayout(w)
            self.v_object = QLineEdit()
            self.v_object.setPlaceholderText("ex.: M42, Jupiter, SS Cyg")
            self.v_desc = QTextEdit()
            self.v_desc.setPlaceholderText("Descricao da observacao visual...")
            self.v_desc.setMaximumHeight(100)
            self.v_conditions = QLineEdit()
            self.v_conditions.setPlaceholderText("ceu, transparência, vento...")
            self.v_seeing = QLineEdit()
            self.v_mag = QDoubleSpinBox()
            self.v_mag.setRange(-5.0, 25.0)
            self.v_mag.setDecimals(2)
            self.v_mag.setSpecialValueText("(sem mag)")
            self.v_mag.setValue(-5.0)
            self.v_observer = QLineEdit("AstroCitizen")
            self.v_when = QLineEdit()
            self.v_when.setPlaceholderText("UTC ISO (vazio = agora)")
            self.v_site = QComboBox()
            self.v_prog = QComboBox()
            self.v_target = QComboBox()
            form.addRow("Objecto", self.v_object)
            form.addRow("Descricao", self.v_desc)
            form.addRow("Condicoes", self.v_conditions)
            form.addRow("Seeing", self.v_seeing)
            form.addRow("Magnitude", self.v_mag)
            form.addRow("Observador", self.v_observer)
            form.addRow("Quando UTC", self.v_when)
            form.addRow("Site", self.v_site)
            form.addRow("Programa", self.v_prog)
            form.addRow("Alvo (opcional)", self.v_target)
            btn = QPushButton("Guardar log visual")
            btn.clicked.connect(self._run_visual)
            form.addRow(btn)
            return w

        def _browse_fits(self) -> None:
            path, _ = QFileDialog.getOpenFileName(
                self, "FITS solar", "", "FITS (*.fits *.fit *.fts);;All (*)"
            )
            if path:
                self.s_path.setText(path)

        def _run_solar(self) -> None:
            ws = self._workspace()
            if ws is None:
                return
            if not (
                self.s_filter_ok.isChecked()
                and self.s_no_eyepiece.isChecked()
                and self.s_daytime.isChecked()
            ):
                QMessageBox.warning(
                    self,
                    "Seguranca solar",
                    "Marque os tres itens do checklist antes de continuar.",
                )
                return
            path = Path(self.s_path.text().strip())
            if not path.is_file():
                QMessageBox.warning(self, "Solar", "Ficheiro FITS invalido.")
                return
            store = LocalArtifactStore(self.artifacts_root)
            uri = store.put(path, key=f"import/solar/{path.name}")
            spots = self.s_spots.value()
            groups = self.s_groups.value()
            try:
                product = CountSunspots(self.archive, store).execute(
                    workspace_id=ws.id,
                    fits_uri=uri,
                    filter_confirmed=True,
                    no_unfiltered_eyepiece=True,
                    daytime_acknowledged=True,
                    filter_name=self.s_filter_name.text().strip() or "white-light",
                    observer=self.s_observer.text().strip() or "AstroCitizen",
                    k=float(self.s_k.value()),
                    spots=None if spots < 0 else int(spots),
                    groups=None if groups < 0 else int(groups),
                    program_id=self.s_prog.currentData(),
                )
            except DomainError as exc:
                QMessageBox.critical(self, "Solar", str(exc))
                return
            self._last_solar_id = product.id
            self._append(
                f"solar product={product.id}  groups={product.summary.get('groups')}  "
                f"spots={product.summary.get('spots')}  "
                f"wolf_r={product.summary.get('wolf_r')}"
            )
            if self.on_changed:
                self.on_changed()

        def _export_solar(self) -> None:
            if self._last_solar_id is None:
                QMessageBox.information(self, "Solar", "Corra Contar manchas primeiro.")
                return
            out_dir = self.artifacts_root / "export" / "solar"
            out_dir.mkdir(parents=True, exist_ok=True)
            out = out_dir / f"{self._last_solar_id}.txt"
            try:
                ExportSolarReport(self.archive).execute(
                    product_id=self._last_solar_id,
                    out_path=out,
                    observer=self.s_observer.text().strip() or None,
                    site=(
                        self.s_site.currentText()
                        if self.s_site.currentData() is not None
                        else None
                    ),
                )
            except DomainError as exc:
                QMessageBox.critical(self, "Solar", str(exc))
                return
            self._append(f"export solar -> {out}")
            QMessageBox.information(self, "Solar", f"Escrito:\n{out}")

        def _run_visual(self) -> None:
            ws = self._workspace()
            if ws is None:
                return
            obj = self.v_object.text().strip()
            tgt = self.v_target.currentData()
            if not obj and tgt is not None:
                t = self.archive.get_target(tgt)
                obj = t.designation if t else ""
            mag_v = float(self.v_mag.value())
            magnitude = None if mag_v <= -5.0 else mag_v
            when = self.v_when.text().strip() or None
            try:
                product = LogVisualObservation(self.archive).execute(
                    workspace_id=ws.id,
                    object_name=obj,
                    description=self.v_desc.toPlainText(),
                    conditions=self.v_conditions.text().strip(),
                    site_id=self.v_site.currentData(),
                    program_id=self.v_prog.currentData(),
                    target_id=tgt,
                    observer=self.v_observer.text().strip() or "AstroCitizen",
                    observed_at_utc=when,
                    magnitude=magnitude,
                    seeing=self.v_seeing.text().strip() or None,
                )
            except DomainError as exc:
                QMessageBox.critical(self, "Visual", str(exc))
                return
            self._append(
                f"visual_log product={product.id}  object={product.summary.get('object')}  "
                f"at={product.summary.get('observed_at_utc')}"
            )
            self.v_desc.clear()
            if self.on_changed:
                self.on_changed()

    return ObserveDashboard
