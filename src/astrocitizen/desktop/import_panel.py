"""Painel Import: FITS externos (canal IN-IMP)."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def import_result_rows(observations: list[Any]) -> list[list[str]]:
    rows: list[list[str]] = []
    for obs in observations:
        hdr = getattr(obs, "headers_summary", None) or {}
        obj = hdr.get("OBJECT") or hdr.get("OBJNAME") or "-"
        rows.append(
            [
                str(getattr(obs, "id", ""))[:8],
                str(getattr(obs, "observed_at_utc", "") or ""),
                str(obj),
                str(getattr(obs, "state", "") or ""),
                "sim" if getattr(obs, "simulated", False) else "real",
            ]
        )
    return rows


def build_import_dashboard(parent: Any | None = None) -> Any:
    """Devolve ImportDashboard (requer PySide6)."""
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
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )

    from astrocitizen.adapters.fs import LocalArtifactStore
    from astrocitizen.observatory import ImportFits
    from astrocitizen.observatory.import_fits import discover_fits_paths
    from astrocitizen.shared.paths import default_artifacts_root

    class ImportDashboard(QWidget):
        def __init__(self, archive: Any, *, artifacts_root: Path | None = None) -> None:
            super().__init__(parent)
            self.archive = archive
            self.artifacts_root = Path(artifacts_root or default_artifacts_root())
            self._workspace_id = None
            self._sites: list[Any] = []
            self._programs: list[Any] = []
            self._last_paths: list[Path] = []

            title = QLabel("Importar FITS (IN-IMP)")
            title.setObjectName("pageTitle")

            form = QFormLayout()
            self.path_edit = QLineEdit()
            self.path_edit.setPlaceholderText("Ficheiro .fits ou pasta...")
            browse_f = QPushButton("Ficheiro...")
            browse_f.setObjectName("secondaryBtn")
            browse_f.clicked.connect(self._browse_file)
            browse_d = QPushButton("Pasta...")
            browse_d.setObjectName("secondaryBtn")
            browse_d.clicked.connect(self._browse_dir)
            path_row = QHBoxLayout()
            path_row.addWidget(self.path_edit, 1)
            path_row.addWidget(browse_f)
            path_row.addWidget(browse_d)
            path_wrap = QWidget()
            path_wrap.setLayout(path_row)
            form.addRow("Caminho", path_wrap)

            self.site_combo = QComboBox()
            self.program_combo = QComboBox()
            self.frame_combo = QComboBox()
            self.frame_combo.addItem("(header)", None)
            for ft in ("light", "bias", "dark", "flat"):
                self.frame_combo.addItem(ft, ft)
            self.recursive = QCheckBox("Recursivo (pastas)")
            self.simulated = QCheckBox("Marcar como simulated")
            form.addRow("Site", self.site_combo)
            form.addRow("Programa", self.program_combo)
            form.addRow("IMAGETYP", self.frame_combo)
            form.addRow("", self.recursive)
            form.addRow("", self.simulated)

            self.import_btn = QPushButton("Importar")
            self.import_btn.clicked.connect(self.run_import)
            self.status = QLabel("Seleccione FITS ou pasta.")
            self.status.setObjectName("emptyState")

            self.table = QTableWidget(0, 5)
            self.table.setAlternatingRowColors(True)
            self.table.setHorizontalHeaderLabels(
                ["Obs", "Quando", "OBJECT", "Estado", "Sim"]
            )
            self.table.horizontalHeader().setStretchLastSection(True)

            root = QVBoxLayout(self)
            root.setContentsMargins(16, 12, 16, 12)
            root.addWidget(title)
            root.addLayout(form)
            root.addWidget(self.import_btn)
            root.addWidget(self.status)
            root.addWidget(self.table, 1)

        def load_workspace(self) -> None:
            self.site_combo.clear()
            self.program_combo.clear()
            self._sites = []
            self._programs = []
            workspaces = self.archive.list_workspaces()
            if not workspaces:
                self.status.setText("Sem workspace. Rode: astrocitizen init-db")
                return
            self._workspace_id = workspaces[0].id
            self.site_combo.addItem("(nenhum)", None)
            self._sites = self.archive.list_sites(self._workspace_id)
            for s in self._sites:
                self.site_combo.addItem(s.name, s.id)
            self.program_combo.addItem("(nenhum)", None)
            self._programs = self.archive.list_programs(self._workspace_id)
            for p in self._programs:
                self.program_combo.addItem(f"{p.template_id} | {p.name}", p.id)

        def _browse_file(self) -> None:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "FITS",
                "",
                "FITS (*.fits *.fit *.fts);;Todos (*)",
            )
            if path:
                self.path_edit.setText(path)

        def _browse_dir(self) -> None:
            d = QFileDialog.getExistingDirectory(self, "Pasta com FITS")
            if d:
                self.path_edit.setText(d)

        def run_import(self) -> None:
            if self._workspace_id is None:
                QMessageBox.warning(self, "Import", "Sem workspace.")
                return
            raw = self.path_edit.text().strip()
            if not raw:
                QMessageBox.warning(self, "Import", "Indique um caminho.")
                return
            try:
                paths = discover_fits_paths(
                    Path(raw), recursive=self.recursive.isChecked()
                )
                store = LocalArtifactStore(self.artifacts_root)
                obs_list = ImportFits(self.archive, store).execute(
                    workspace_id=self._workspace_id,
                    paths=paths,
                    site_id=self.site_combo.currentData(),
                    program_id=self.program_combo.currentData(),
                    frame_type=self.frame_combo.currentData(),
                    simulated=self.simulated.isChecked(),
                )
            except Exception as exc:  # noqa: BLE001 - UI boundary
                QMessageBox.critical(self, "Import", str(exc))
                self.status.setText(f"erro: {exc}")
                return
            self._last_paths = paths
            rows = import_result_rows(obs_list)
            self.table.setRowCount(len(rows))
            for r, row in enumerate(rows):
                for c, val in enumerate(row):
                    self.table.setItem(r, c, QTableWidgetItem(val))
            self.status.setText(f"Importados {len(obs_list)} FITS.")
            QMessageBox.information(
                self, "Import", f"Importados {len(obs_list)} ficheiro(s)."
            )

    return ImportDashboard
