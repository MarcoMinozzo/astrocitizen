"""Painel Radio: import serie / espectro / scan (PO-I01..I04 / AC-161)."""

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
    from astrocitizen.observatory import (
        ImportRadioScan,
        ImportRadioSpectrum,
        ImportRadioTimeseries,
    )
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
            title = QLabel("Radio — IN-RAD (PO-I01..I04)")
            title.setObjectName("pageTitle")
            root.addWidget(title)

            self.hint = QLabel("")
            self.hint.setObjectName("emptyState")
            self.hint.setWordWrap(True)
            root.addWidget(self.hint)

            form = QFormLayout()
            self.kind = QComboBox()
            self.kind.addItem("Serie potencia (I01/I04)", "series")
            self.kind.addItem("Espectro RF (I02)", "spectrum")
            self.kind.addItem("Drift / scan (I03)", "scan")
            self.kind.currentIndexChanged.connect(self._update_hint)
            form.addRow("Modo", self.kind)

            self.path = QLineEdit()
            browse = QPushButton("Ficheiro...")
            browse.setObjectName("secondaryBtn")
            browse.clicked.connect(self._browse)
            prow = QHBoxLayout()
            prow.addWidget(self.path, 1)
            prow.addWidget(browse)
            pwrap = QWidget()
            pwrap.setLayout(prow)
            form.addRow("Ficheiro", pwrap)

            self.site = QComboBox()
            self.program = QComboBox()
            self.observer = QLineEdit("AstroCitizen")
            self.freq = QLineEdit()
            self.freq.setPlaceholderText("MHz (opcional)")
            self.notes = QLineEdit()
            self.lab_notes = QLineEdit()
            self.lab_notes.setPlaceholderText("Construcao / lab (PO-I04)")
            form.addRow("Site", self.site)
            form.addRow("Programa", self.program)
            form.addRow("Observer", self.observer)
            form.addRow("Freq MHz", self.freq)
            form.addRow("Notes", self.notes)
            form.addRow("Lab notes", self.lab_notes)

            btn = QPushButton("Importar radio")
            btn.clicked.connect(self._import)
            form.addRow(btn)
            root.addLayout(form)

            self.log = QTextEdit()
            self.log.setReadOnly(True)
            root.addWidget(self.log, 1)
            self._update_hint()

        def _update_hint(self) -> None:
            kind = str(self.kind.currentData() or "series")
            tips = {
                "series": (
                    "CSV t_utc,power[,power_err] ou HDF5 (h5py). "
                    "Produto radio_timeseries. Lab notes opcionais (I04)."
                ),
                "spectrum": (
                    "CSV freq_mhz,power[,power_err]. Produto radio_spectrum (HI 21 cm)."
                ),
                "scan": (
                    "CSV t_utc,power[,az_deg|el_deg|ha_deg]. Produto radio_scan (drift)."
                ),
            }
            self.hint.setText(tips.get(kind, tips["series"]))

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

        def set_shell_context(
            self, *, site_id: object = None, program_id: object = None
        ) -> None:
            from astrocitizen.desktop.widgets import select_combo_data

            select_combo_data(self.site, site_id)
            select_combo_data(self.program, program_id)

        def focus_kind(self, kind: str | None) -> None:
            if not kind:
                return
            i = self.kind.findData(str(kind).lower())
            if i >= 0:
                self.kind.setCurrentIndex(i)

        def _browse(self) -> None:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Ficheiro radio",
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
            kind = str(self.kind.currentData() or "series")
            store = LocalArtifactStore(self.artifacts_root)
            common = dict(
                workspace_id=ws.id,
                path=path,
                site_id=self.site.currentData(),
                program_id=self.program.currentData(),
                observer=self.observer.text().strip() or "AstroCitizen",
                frequency_mhz=freq,
                notes=self.notes.text().strip(),
                lab_notes=self.lab_notes.text().strip(),
            )
            try:
                if kind == "spectrum":
                    product = ImportRadioSpectrum(self.archive, store).execute(**common)
                elif kind == "scan":
                    product = ImportRadioScan(self.archive, store).execute(**common)
                else:
                    product = ImportRadioTimeseries(self.archive, store).execute(
                        **common
                    )
            except DomainError as exc:
                QMessageBox.critical(self, "Radio", str(exc))
                return
            self._product_id = product.id
            extra = ""
            if product.product_type == "radio_spectrum":
                extra = (
                    f"  f={product.summary.get('freq0_mhz')}-"
                    f"{product.summary.get('freq1_mhz')}MHz"
                )
            self._append(
                f"product={product.id}  type={product.product_type}  "
                f"n={product.summary.get('n_points')}  "
                f"fmt={product.summary.get('format')}  "
                f"pmin={product.summary.get('power_min')}  "
                f"pmax={product.summary.get('power_max')}{extra}"
            )
            if self.on_changed:
                self.on_changed()

    return RadioDashboard
