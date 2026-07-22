"""Painel Especialidades: echelle / speckle / polar (ENTRADA #7 / P4)."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def build_specialty_dashboard() -> type:
    from PySide6.QtWidgets import (
        QComboBox,
        QFileDialog,
        QFormLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMessageBox,
        QPushButton,
        QTabWidget,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    from astrocitizen.adapters.fs import LocalArtifactStore
    from astrocitizen.observatory import (
        ImportEchelleOrders,
        ImportPolarimetrySet,
        ImportSpeckleCube,
    )
    from astrocitizen.shared.errors import DomainError
    from astrocitizen.shared.paths import default_artifacts_root

    class SpecialtyDashboard(QWidget):
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

            root = QVBoxLayout(self)
            root.setContentsMargins(16, 12, 16, 12)
            title = QLabel("Especialidades — Echelle / Speckle / Polar (P4)")
            title.setObjectName("pageTitle")
            root.addWidget(title)

            hint = QLabel(
                "Entrada de dados para PO-B07, PO-G02 e PO-H01. "
                "Reducao cientifica completa fica em waves seguintes."
            )
            hint.setObjectName("emptyState")
            hint.setWordWrap(True)
            root.addWidget(hint)

            self.site = QComboBox()
            self.program = QComboBox()
            meta = QFormLayout()
            meta.addRow("Site", self.site)
            meta.addRow("Programa", self.program)
            root.addLayout(meta)

            tabs = QTabWidget()
            tabs.addTab(self._tab_echelle(), "Echelle")
            tabs.addTab(self._tab_speckle(), "Speckle")
            tabs.addTab(self._tab_polar(), "Polar")
            root.addWidget(tabs)

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

        def _path_row(self, edit: QLineEdit, browse_cb: Any, label: str = "...") -> QWidget:
            browse = QPushButton(label)
            browse.setObjectName("secondaryBtn")
            browse.clicked.connect(browse_cb)
            row = QHBoxLayout()
            row.addWidget(edit, 1)
            row.addWidget(browse)
            wrap = QWidget()
            wrap.setLayout(row)
            return wrap

        def _tab_echelle(self) -> QWidget:
            w = QWidget()
            form = QFormLayout(w)
            self.ech_path = QLineEdit()
            form.addRow(
                "FITS/pasta",
                self._path_row(self.ech_path, self._browse_ech, "Abrir..."),
            )
            btn = QPushButton("Importar echelle")
            btn.clicked.connect(self._import_ech)
            form.addRow(btn)
            return w

        def _tab_speckle(self) -> QWidget:
            w = QWidget()
            form = QFormLayout(w)
            self.spk_path = QLineEdit()
            form.addRow(
                "Cubo/pasta/SER",
                self._path_row(self.spk_path, self._browse_spk, "Abrir..."),
            )
            btn = QPushButton("Importar speckle")
            btn.clicked.connect(self._import_spk)
            form.addRow(btn)
            return w

        def _tab_polar(self) -> QWidget:
            w = QWidget()
            form = QFormLayout(w)
            self.pol_path = QLineEdit()
            self.pol_angles = QLineEdit()
            form.addRow(
                "Frames",
                self._path_row(self.pol_path, self._browse_pol, "Abrir..."),
            )
            form.addRow(
                "Angles CSV",
                self._path_row(self.pol_angles, self._browse_angles, "CSV..."),
            )
            btn = QPushButton("Importar polar")
            btn.clicked.connect(self._import_pol)
            form.addRow(btn)
            return w

        def _browse_ech(self) -> None:
            path, _ = QFileDialog.getOpenFileName(
                self, "Echelle", "", "FITS (*.fits *.fit *.fts);;All (*)"
            )
            if path:
                self.ech_path.setText(path)

        def _browse_spk(self) -> None:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Speckle",
                "",
                "Data (*.fits *.fit *.ser *.avi);;All (*)",
            )
            if path:
                self.spk_path.setText(path)

        def _browse_pol(self) -> None:
            path = QFileDialog.getExistingDirectory(self, "Pasta polar")
            if path:
                self.pol_path.setText(path)

        def _browse_angles(self) -> None:
            path, _ = QFileDialog.getOpenFileName(
                self, "Angles", "", "CSV (*.csv *.txt);;All (*)"
            )
            if path:
                self.pol_angles.setText(path)

        def _import_ech(self) -> None:
            ws = self._workspace()
            if ws is None:
                return
            path = Path(self.ech_path.text().strip())
            store = LocalArtifactStore(self.artifacts_root)
            try:
                product = ImportEchelleOrders(self.archive, store).execute(
                    workspace_id=ws.id,
                    path=path,
                    site_id=self.site.currentData(),
                    program_id=self.program.currentData(),
                )
            except DomainError as exc:
                QMessageBox.critical(self, "Echelle", str(exc))
                return
            self._append(
                f"echelle={product.id}  orders={product.summary.get('n_orders')}"
            )
            if self.on_changed:
                self.on_changed()

        def _import_spk(self) -> None:
            ws = self._workspace()
            if ws is None:
                return
            path = Path(self.spk_path.text().strip())
            store = LocalArtifactStore(self.artifacts_root)
            try:
                product = ImportSpeckleCube(self.archive, store).execute(
                    workspace_id=ws.id,
                    path=path,
                    site_id=self.site.currentData(),
                    program_id=self.program.currentData(),
                )
            except DomainError as exc:
                QMessageBox.critical(self, "Speckle", str(exc))
                return
            self._append(
                f"speckle={product.id}  frames={product.summary.get('n_frames')}  "
                f"fmt={product.summary.get('format')}"
            )
            if self.on_changed:
                self.on_changed()

        def _import_pol(self) -> None:
            ws = self._workspace()
            if ws is None:
                return
            path = Path(self.pol_path.text().strip())
            atxt = self.pol_angles.text().strip()
            store = LocalArtifactStore(self.artifacts_root)
            try:
                product = ImportPolarimetrySet(self.archive, store).execute(
                    workspace_id=ws.id,
                    path=path,
                    angles_csv=Path(atxt) if atxt else None,
                    site_id=self.site.currentData(),
                    program_id=self.program.currentData(),
                )
            except DomainError as exc:
                QMessageBox.critical(self, "Polar", str(exc))
                return
            self._append(
                f"polar={product.id}  n={product.summary.get('n_frames')}  "
                f"P={product.summary.get('P')}  theta={product.summary.get('theta_deg')}"
            )
            if self.on_changed:
                self.on_changed()

    return SpecialtyDashboard
