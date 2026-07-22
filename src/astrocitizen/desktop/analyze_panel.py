"""Painel Analisar: bridges + viewer FITS + curvas (U3/U4/U5)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID


def build_analyze_dashboard() -> type:
    from PySide6.QtGui import QImage, QPixmap
    from PySide6.QtWidgets import (
        QDoubleSpinBox,
        QFileDialog,
        QFormLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMessageBox,
        QPushButton,
        QScrollArea,
        QTabWidget,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    from astrocitizen.adapters.fs import LocalArtifactStore
    from astrocitizen.analysis import (
        AperturePhotometry,
        BlinkDiff,
        ExtractSpectrum1D,
    )
    from astrocitizen.desktop.plot_widget import build_series_plot
    from astrocitizen.desktop.series import series_from_measurement_points
    from astrocitizen.reduction import fits_stats, stretch_display
    from astrocitizen.shared.errors import DomainError
    from astrocitizen.shared.paths import default_artifacts_root

    SeriesPlot = build_series_plot()

    class AnalyzeDashboard(QWidget):
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
            self._shell_program_id = None

            root = QVBoxLayout(self)
            root.setContentsMargins(16, 12, 16, 12)
            title = QLabel("Analisar")
            title.setObjectName("pageTitle")
            root.addWidget(title)
            hint = QLabel(
                "Bridges GUI dos pipelines CLI. Importacao de dados fica em "
                "Observatorio → Importar."
            )
            hint.setObjectName("emptyState")
            hint.setWordWrap(True)
            hint.setStyleSheet("padding: 0 0 8px 0;")
            root.addWidget(hint)

            self.tabs = QTabWidget()
            self.tabs.addTab(self._tab_photometry(), "Fotometria")
            self.tabs.addTab(self._tab_spectrum(), "Espectro")
            self.tabs.addTab(self._tab_blink(), "Blink / Astrom")
            self.tabs.addTab(self._tab_viewer(), "Viewer FITS")
            self.tabs.addTab(self._tab_curves(), "Curvas")
            root.addWidget(self.tabs, 1)

            self.log = QTextEdit()
            self.log.setReadOnly(True)
            self.log.setMaximumHeight(140)
            root.addWidget(self.log)

        def _append(self, msg: str) -> None:
            self.log.append(msg)

        def _workspace(self):
            ws = self.archive.list_workspaces()
            return ws[0] if ws else None

        def set_shell_context(
            self, *, site_id: object = None, program_id: object = None
        ) -> None:
            self._shell_program_id = program_id

        def reload(self) -> None:
            return None

        def _path_row(self, edit: QLineEdit, slot: Any) -> QWidget:
            browse = QPushButton("Ficheiro...")
            browse.setObjectName("secondaryBtn")
            browse.clicked.connect(slot)
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.addWidget(edit, 1)
            row.addWidget(browse)
            w = QWidget()
            w.setLayout(row)
            return w

        def _put_fits(self, path: Path) -> str:
            store = LocalArtifactStore(self.artifacts_root)
            return store.put(path, key=f"analysis/gui/{path.name}")

        def _tab_photometry(self) -> QWidget:
            w = QWidget()
            form = QFormLayout(w)
            self.ph_path = QLineEdit()
            form.addRow(
                "FITS",
                self._path_row(self.ph_path, lambda: self._browse(self.ph_path)),
            )
            self.ph_x = QDoubleSpinBox()
            self.ph_x.setRange(0, 1e5)
            self.ph_x.setValue(100)
            self.ph_y = QDoubleSpinBox()
            self.ph_y.setRange(0, 1e5)
            self.ph_y.setValue(100)
            self.ph_band = QLineEdit("V")
            form.addRow("X", self.ph_x)
            form.addRow("Y", self.ph_y)
            form.addRow("Band", self.ph_band)
            btn = QPushButton("Correr fotometria")
            btn.clicked.connect(self._run_photometry)
            form.addRow(btn)
            return w

        def _tab_spectrum(self) -> QWidget:
            w = QWidget()
            form = QFormLayout(w)
            self.sp_path = QLineEdit()
            form.addRow(
                "FITS 2D",
                self._path_row(self.sp_path, lambda: self._browse(self.sp_path)),
            )
            self.sp_trace = QDoubleSpinBox()
            self.sp_trace.setRange(0, 1e5)
            self.sp_trace.setValue(50)
            self.sp_hw = QDoubleSpinBox()
            self.sp_hw.setRange(1, 50)
            self.sp_hw.setValue(3)
            form.addRow("Trace Y", self.sp_trace)
            form.addRow("Half-width", self.sp_hw)
            btn = QPushButton("Extrair espectro 1D")
            btn.clicked.connect(self._run_spectrum)
            form.addRow(btn)
            return w

        def _tab_blink(self) -> QWidget:
            w = QWidget()
            form = QFormLayout(w)
            self.bl_new = QLineEdit()
            self.bl_ref = QLineEdit()
            form.addRow(
                "New FITS",
                self._path_row(self.bl_new, lambda: self._browse(self.bl_new)),
            )
            form.addRow(
                "Ref FITS",
                self._path_row(self.bl_ref, lambda: self._browse(self.bl_ref)),
            )
            btn = QPushButton("Blink diff")
            btn.clicked.connect(self._run_blink)
            form.addRow(btn)
            return w

        def _tab_viewer(self) -> QWidget:
            w = QWidget()
            lay = QVBoxLayout(w)
            form = QFormLayout()
            self.vw_path = QLineEdit()
            form.addRow(
                "FITS",
                self._path_row(self.vw_path, lambda: self._browse(self.vw_path)),
            )
            btn = QPushButton("Abrir / stretch")
            btn.clicked.connect(self._run_viewer)
            form.addRow(btn)
            lay.addLayout(form)
            self.vw_stats = QLabel("Sem imagem.")
            self.vw_stats.setObjectName("emptyState")
            self.vw_stats.setWordWrap(True)
            lay.addWidget(self.vw_stats)
            self.vw_image = QLabel()
            self.vw_image.setObjectName("radarPane")
            self.vw_image.setMinimumHeight(240)
            self.vw_image.setScaledContents(False)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(self.vw_image)
            lay.addWidget(scroll, 1)
            return w

        def _tab_curves(self) -> QWidget:
            w = QWidget()
            lay = QVBoxLayout(w)
            form = QFormLayout()
            self.cu_product = QLineEdit()
            self.cu_product.setPlaceholderText("UUID do analysis_product")
            form.addRow("Product ID", self.cu_product)
            btn = QPushButton("Carregar curva")
            btn.clicked.connect(self._run_curves)
            form.addRow(btn)
            lay.addLayout(form)
            self.cu_info = QLabel("Cole o UUID apos fotometria/espectro, ou escolha em Arquivo.")
            self.cu_info.setObjectName("emptyState")
            self.cu_info.setWordWrap(True)
            lay.addWidget(self.cu_info)
            self.cu_plot = SeriesPlot()
            lay.addWidget(self.cu_plot, 1)
            return w

        def _run_curves(self) -> None:
            raw = self.cu_product.text().strip()
            if not raw:
                QMessageBox.warning(self, "Curvas", "Indique o product UUID.")
                return
            try:
                pid = UUID(raw)
            except ValueError:
                QMessageBox.warning(self, "Curvas", "UUID invalido.")
                return
            product = self.archive.get_analysis_product(pid)
            if product is None:
                QMessageBox.warning(self, "Curvas", "Produto nao encontrado.")
                return
            points = self.archive.list_measurement_points(pid)
            xs, ys, band = series_from_measurement_points(points)
            if len(xs) < 2:
                self.cu_plot.clear()
                self.cu_info.setText(
                    f"{product.product_type}: {len(points)} pontos brutos, "
                    f"{len(xs)} validos (precisa >=2)."
                )
                return
            self.cu_plot.set_series(
                xs,
                ys,
                title=f"{product.product_type}  ({len(xs)} pts)",
                xlabel="x",
                ylabel=band,
            )
            self.cu_info.setText(
                f"OK  type={product.product_type}  state={product.state}  n={len(xs)}"
            )
            self._append(f"curve plot  product={pid}  n={len(xs)}")

        def _browse(self, edit: QLineEdit) -> None:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "FITS",
                "",
                "FITS (*.fits *.fit *.fts);;All (*)",
            )
            if path:
                edit.setText(path)

        def _run_photometry(self) -> None:
            ws = self._workspace()
            if ws is None:
                return
            path = Path(self.ph_path.text().strip())
            if not path.is_file():
                QMessageBox.warning(self, "Analisar", "FITS invalido.")
                return
            store = LocalArtifactStore(self.artifacts_root)
            try:
                uri = self._put_fits(path)
                product = AperturePhotometry(self.archive, store).execute(
                    workspace_id=ws.id,
                    fits_uri=uri,
                    x=float(self.ph_x.value()),
                    y=float(self.ph_y.value()),
                    band=self.ph_band.text().strip() or "V",
                    program_id=self._shell_program_id,
                )
            except (DomainError, ValueError, OSError) as exc:
                QMessageBox.critical(self, "Analisar", str(exc))
                return
            self._append(
                f"photometry={product.id}  mag={product.summary.get('mag')}  "
                f"flux={product.summary.get('flux')}"
            )
            self.cu_product.setText(str(product.id))
            if self.on_changed:
                self.on_changed()

        def _run_spectrum(self) -> None:
            ws = self._workspace()
            if ws is None:
                return
            path = Path(self.sp_path.text().strip())
            if not path.is_file():
                QMessageBox.warning(self, "Analisar", "FITS invalido.")
                return
            store = LocalArtifactStore(self.artifacts_root)
            try:
                uri = self._put_fits(path)
                product = ExtractSpectrum1D(self.archive, store).execute(
                    workspace_id=ws.id,
                    fits_uri=uri,
                    trace_y=float(self.sp_trace.value()),
                    half_width=int(self.sp_hw.value()),
                    program_id=self._shell_program_id,
                )
            except (DomainError, ValueError, OSError) as exc:
                QMessageBox.critical(self, "Analisar", str(exc))
                return
            self._append(
                f"spectrum={product.id}  "
                f"wave={product.summary.get('wave0_nm')}-{product.summary.get('wave1_nm')}nm"
            )
            self.cu_product.setText(str(product.id))
            if self.on_changed:
                self.on_changed()

        def _run_blink(self) -> None:
            ws = self._workspace()
            if ws is None:
                return
            new_p = Path(self.bl_new.text().strip())
            ref_p = Path(self.bl_ref.text().strip())
            if not new_p.is_file() or not ref_p.is_file():
                QMessageBox.warning(self, "Analisar", "Indique new e ref FITS.")
                return
            store = LocalArtifactStore(self.artifacts_root)
            try:
                new_uri = self._put_fits(new_p)
                ref_uri = store.put(ref_p, key=f"analysis/gui/{ref_p.name}")
                product = BlinkDiff(self.archive, store).execute(
                    workspace_id=ws.id,
                    new_uri=new_uri,
                    ref_uri=ref_uri,
                    program_id=self._shell_program_id,
                )
            except (DomainError, ValueError, OSError) as exc:
                QMessageBox.critical(self, "Analisar", str(exc))
                return
            self._append(
                f"blink={product.id}  peak={product.summary.get('peak')}  "
                f"snr={product.summary.get('snr')}"
            )
            if self.on_changed:
                self.on_changed()

        def _run_viewer(self) -> None:
            import numpy as np
            from astropy.io import fits

            path = Path(self.vw_path.text().strip())
            if not path.is_file():
                QMessageBox.warning(self, "Viewer", "FITS invalido.")
                return
            try:
                st = fits_stats(path)
                with fits.open(path) as hdul:
                    data = np.asarray(hdul[0].data, dtype=np.float64)
                if data.ndim > 2:
                    data = data[0]
                disp = stretch_display(data)
                disp = np.ascontiguousarray(disp)
                h, w = disp.shape
                qimg = QImage(
                    disp.data,
                    w,
                    h,
                    w,
                    QImage.Format.Format_Grayscale8,
                ).copy()
                pix = QPixmap.fromImage(qimg)
                if pix.width() > 900:
                    pix = pix.scaledToWidth(900)
                self.vw_image.setPixmap(pix)
                self.vw_stats.setText(
                    f"OBJECT={st.get('object')}  EXPTIME={st.get('exptime')}  "
                    f"shape={st.get('shape')}  med={st.get('median'):.3g}  "
                    f"p1={st.get('p1'):.3g}  p99={st.get('p99'):.3g}"
                )
                self._append(f"viewer OK  {path.name}  shape={st.get('shape')}")
            except Exception as exc:  # noqa: BLE001 - UI boundary
                QMessageBox.critical(self, "Viewer", str(exc))

    return AnalyzeDashboard
