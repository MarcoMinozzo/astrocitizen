"""Painel Radio: import potencia vs tempo (PO-I01 / ENTRADA #6)."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def build_radio_dashboard() -> type:
    from PySide6.QtWidgets import (
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
    from astrocitizen.observatory import ImportRadioTimeseries
    from astrocitizen.shared.errors import DomainError
    from astrocitizen.shared.paths import default_artifacts_root

    class RadioDashboard(QWidget):
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
            self._product_id = None

            root = QVBoxLayout(self)
            root.setContentsMargins(16, 12, 16, 12)
            title = QLabel("Radio — serie potencia (PO-I01)")
            title.setObjectName("pageTitle")
            root.addWidget(title)

            hint = QLabel(
                "Importar CSV (t_utc,power) ou HDF5 (h5py). "
                "Cria Observation + radio_timeseries + measurement_points."
            )
            hint.setObjectName("emptyState")
            hint.setWordWrap(True)
            root.addWidget(hint)

            form = QFormLayout()
            self.path = QLineEdit()
            browse = QPushButton("Ficheiro...")
            browse.setObjectName("secondaryBtn")
            browse.clicked.connect(self._browse)
            prow = QHBoxLayout()
            prow.addWidget(self.path, 1)
            prow.addWidget(browse)
            pwrap = QWidget()
            pwrap.setLayout(prow)
            form.addRow("Serie", pwrap)

            self.site = QComboBox()
            self.program = QComboBox()
            self.observer = QLineEdit("AstroCitizen")
            self.freq = QLineEdit()
            self.freq.setPlaceholderText("MHz (opcional)")
            self.notes = QLineEdit()
            form.addRow("Site", self.site)
            form.addRow("Programa", self.program)
            form.addRow("Observer", self.observer)
            form.addRow("Freq MHz", self.freq)
            form.addRow("Notes", self.notes)

            btn = QPushButton("Importar radio")
            btn.clicked.connect(self._import)
            form.addRow(btn)
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

        def _browse(self) -> None:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Serie radio",
                "",
                "Radio (*.csv *.txt *.h5 *.hdf5);;All (*)",
            )
            if path:
                self.path.setText(path)

        def _import(self) -> None:
            ws = self._workspace()
            if ws is None:
                return
            path = Path(self.path.text().strip())
            if not path.is_file():
                QMessageBox.warning(self, "Radio", "Ficheiro invalido.")
                return
            freq = None
            ftxt = self.freq.text().strip()
            if ftxt:
                try:
                    freq = float(ftxt)
                except ValueError:
                    QMessageBox.warning(self, "Radio", "Freq MHz invalida.")
                    return
            store = LocalArtifactStore(self.artifacts_root)
            try:
                product = ImportRadioTimeseries(self.archive, store).execute(
                    workspace_id=ws.id,
                    path=path,
                    site_id=self.site.currentData(),
                    program_id=self.program.currentData(),
                    observer=self.observer.text().strip() or "AstroCitizen",
                    frequency_mhz=freq,
                    notes=self.notes.text().strip(),
                )
            except DomainError as exc:
                QMessageBox.critical(self, "Radio", str(exc))
                return
            self._product_id = product.id
            self._append(
                f"product={product.id}  n={product.summary.get('n_points')}  "
                f"fmt={product.summary.get('format')}  "
                f"pmin={product.summary.get('power_min')}  "
                f"pmax={product.summary.get('power_max')}"
            )
            if self.on_changed:
                self.on_changed()

    return RadioDashboard
