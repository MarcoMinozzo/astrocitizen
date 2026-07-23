"""Painel Analisar: bridges + viewer + curvas + plate-solve + medida astrometria."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID


def parse_optional_float(text: str) -> float | None:
    """Converte texto vazio -> None; senao float (ValueError se invalido)."""
    t = (text or "").strip()
    if not t:
        return None
    return float(t)


def build_analyze_dashboard() -> type:
    from PySide6.QtGui import QImage, QPixmap
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QDoubleSpinBox,
        QFileDialog,
        QFormLayout,
        QGroupBox,
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
    from astrocitizen.adapters.platesolve import create_plate_solver
    from astrocitizen.analysis import (
        AperturePhotometry,
        BlinkDiff,
        ExtractSpectrum1D,
        MeasureAstrometry,
        PlateSolve,
    )
    from astrocitizen.contribution.credentials import LocalCredentialsStore
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

        def focus_tab(self, name: str) -> None:
            for i in range(self.tabs.count()):
                if self.tabs.tabText(i) == name:
                    self.tabs.setCurrentIndex(i)
                    return

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
            self.sp_auto = QCheckBox("Auto-trace (AC-100)")
            self.sp_auto.setChecked(True)
            self.sp_sky = QCheckBox("Subtrair ceu")
            self.sp_sky.setChecked(True)
            form.addRow("Trace Y", self.sp_trace)
            form.addRow("Half-width", self.sp_hw)
            form.addRow(self.sp_auto)
            form.addRow(self.sp_sky)
            btn = QPushButton("Extrair espectro 1D")
            btn.clicked.connect(self._run_spectrum)
            form.addRow(btn)
            return w

        def _tab_blink(self) -> QWidget:
            w = QWidget()
            lay = QVBoxLayout(w)
            lay.setContentsMargins(0, 0, 0, 0)

            blink_box = QGroupBox("Blink diff")
            blink_form = QFormLayout(blink_box)
            self.bl_new = QLineEdit()
            self.bl_ref = QLineEdit()
            blink_form.addRow(
                "New FITS",
                self._path_row(self.bl_new, lambda: self._browse(self.bl_new)),
            )
            blink_form.addRow(
                "Ref FITS",
                self._path_row(self.bl_ref, lambda: self._browse(self.bl_ref)),
            )
            btn_bl = QPushButton("Blink diff")
            btn_bl.clicked.connect(self._run_blink)
            blink_form.addRow(btn_bl)
            lay.addWidget(blink_box)

            ps_box = QGroupBox("Plate-solve / WCS (AC-110)")
            ps_form = QFormLayout(ps_box)
            self.ps_path = QLineEdit()
            ps_form.addRow(
                "FITS",
                self._path_row(self.ps_path, lambda: self._browse(self.ps_path)),
            )
            self.ps_backend = QComboBox()
            for b in ("auto", "solve-field", "nova", "synthetic"):
                self.ps_backend.addItem(b, b)
            self.ps_backend.setCurrentIndex(0)
            ps_form.addRow("Backend", self.ps_backend)
            self.ps_ra = QLineEdit()
            self.ps_ra.setPlaceholderText("RA deg (hint, opcional)")
            self.ps_dec = QLineEdit()
            self.ps_dec.setPlaceholderText("Dec deg (hint, opcional)")
            self.ps_radius = QLineEdit()
            self.ps_radius.setPlaceholderText("raio busca deg")
            self.ps_scale_low = QLineEdit()
            self.ps_scale_low.setPlaceholderText("arcsec/pix")
            self.ps_scale_high = QLineEdit()
            self.ps_scale_high.setPlaceholderText("arcsec/pix")
            ps_form.addRow("RA hint", self.ps_ra)
            ps_form.addRow("Dec hint", self.ps_dec)
            ps_form.addRow("Radius", self.ps_radius)
            ps_form.addRow("Scale low", self.ps_scale_low)
            ps_form.addRow("Scale high", self.ps_scale_high)
            self.ps_nova_submit = QCheckBox("Nova: envio real (--submit)")
            ps_form.addRow(self.ps_nova_submit)
            hint = QLabel(
                "synthetic/auto sem solve-field: hints RA/Dec (+ scale) obrigatorios. "
                "Nova sem submit = dry-run."
            )
            hint.setObjectName("emptyState")
            hint.setWordWrap(True)
            ps_form.addRow(hint)
            btn_ps = QPushButton("Plate-solve")
            btn_ps.clicked.connect(self._run_plate_solve)
            ps_form.addRow(btn_ps)
            lay.addWidget(ps_box)

            as_box = QGroupBox("Medir astrometria (x,y → RA/Dec)")
            as_form = QFormLayout(as_box)
            self.as_path = QLineEdit()
            self.as_path.setPlaceholderText("FITS com WCS (apos plate-solve) ou tan-plane")
            as_form.addRow(
                "FITS",
                self._path_row(self.as_path, lambda: self._browse(self.as_path)),
            )
            self.as_x = QDoubleSpinBox()
            self.as_x.setRange(0, 1e5)
            self.as_x.setDecimals(2)
            self.as_x.setValue(100)
            self.as_y = QDoubleSpinBox()
            self.as_y.setRange(0, 1e5)
            self.as_y.setDecimals(2)
            self.as_y.setValue(100)
            as_form.addRow("X (pix)", self.as_x)
            as_form.addRow("Y (pix)", self.as_y)
            self.as_ra0 = QLineEdit()
            self.as_ra0.setPlaceholderText("RA0 deg se sem WCS")
            self.as_dec0 = QLineEdit()
            self.as_dec0.setPlaceholderText("Dec0 deg se sem WCS")
            self.as_scale = QLineEdit()
            self.as_scale.setPlaceholderText("arcsec/pix se sem WCS")
            self.as_pa = QLineEdit()
            self.as_pa.setPlaceholderText("0")
            self.as_pa.setText("0")
            as_form.addRow("RA0", self.as_ra0)
            as_form.addRow("Dec0", self.as_dec0)
            as_form.addRow("Scale", self.as_scale)
            as_form.addRow("PA deg", self.as_pa)
            self.as_desig = QLineEdit()
            self.as_desig.setPlaceholderText("designacao / OBJECT")
            self.as_band = QLineEdit("R")
            self.as_nonsidereal = QCheckBox("Tracking nao-sideral (PO-C02)")
            as_form.addRow("Designation", self.as_desig)
            as_form.addRow("Band", self.as_band)
            as_form.addRow(self.as_nonsidereal)
            as_hint = QLabel(
                "Com WCS no header (pos plate-solve): so X/Y. "
                "Sem WCS: RA0/Dec0/scale obrigatorios (tan-plane)."
            )
            as_hint.setObjectName("emptyState")
            as_hint.setWordWrap(True)
            as_form.addRow(as_hint)
            btn_as = QPushButton("Medir RA/Dec")
            btn_as.clicked.connect(self._run_astrometry)
            as_form.addRow(btn_as)
            self.as_result = QLabel("")
            self.as_result.setObjectName("emptyState")
            self.as_result.setWordWrap(True)
            as_form.addRow(self.as_result)
            lay.addWidget(as_box)
            lay.addStretch(1)
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
            auto = bool(self.sp_auto.isChecked())
            try:
                uri = self._put_fits(path)
                product = ExtractSpectrum1D(self.archive, store).execute(
                    workspace_id=ws.id,
                    fits_uri=uri,
                    trace_y=None if auto else float(self.sp_trace.value()),
                    half_width=int(self.sp_hw.value()),
                    auto_trace=auto,
                    subtract_sky=bool(self.sp_sky.isChecked()),
                    program_id=self._shell_program_id,
                )
            except (DomainError, ValueError, OSError) as exc:
                QMessageBox.critical(self, "Analisar", str(exc))
                return
            self._append(
                f"spectrum={product.id}  "
                f"trace={product.summary.get('trace_y')}  "
                f"snr={product.summary.get('snr_est')}  "
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

        def _run_plate_solve(self) -> None:
            ws = self._workspace()
            if ws is None:
                return
            path = Path(self.ps_path.text().strip())
            if not path.is_file():
                QMessageBox.warning(self, "Plate-solve", "FITS invalido.")
                return
            try:
                ra = parse_optional_float(self.ps_ra.text())
                dec = parse_optional_float(self.ps_dec.text())
                radius = parse_optional_float(self.ps_radius.text())
                scale_low = parse_optional_float(self.ps_scale_low.text())
                scale_high = parse_optional_float(self.ps_scale_high.text())
            except ValueError:
                QMessageBox.warning(
                    self, "Plate-solve", "Hints numericos invalidos."
                )
                return
            backend = str(self.ps_backend.currentData() or "auto")
            store = LocalArtifactStore(self.artifacts_root)
            cred = LocalCredentialsStore()
            api_key = cred.get_network("astrometrynet").get("api_key")
            try:
                uri = self._put_fits(path)
                nova_dry = not self.ps_nova_submit.isChecked()
                solver = create_plate_solver(
                    backend,
                    api_key=str(api_key) if api_key else None,
                    nova_dry_run=nova_dry if backend == "nova" else True,
                )
                product, result = PlateSolve(self.archive, store, solver).execute(
                    workspace_id=ws.id,
                    fits_uri=uri,
                    ra_hint_deg=ra,
                    dec_hint_deg=dec,
                    radius_deg=radius,
                    scale_low_arcsec=scale_low,
                    scale_high_arcsec=scale_high,
                    program_id=self._shell_program_id,
                )
            except (DomainError, ValueError, OSError) as exc:
                QMessageBox.critical(self, "Plate-solve", str(exc))
                return
            self._append(
                f"wcs={product.id}  backend={result.backend}  "
                f"ra={result.ra_center_deg}  dec={result.dec_center_deg}  "
                f"scale={result.scale_arcsec}  "
                f"wcs_uri={product.parameters.get('wcs_uri')}"
            )
            wcs_uri = product.parameters.get("wcs_uri")
            if wcs_uri and hasattr(self, "as_path"):
                try:
                    self.as_path.setText(str(store.resolve(str(wcs_uri))))
                except (OSError, ValueError, KeyError):
                    pass
            if self.on_changed:
                self.on_changed()

        def _run_astrometry(self) -> None:
            ws = self._workspace()
            if ws is None:
                return
            path = Path(self.as_path.text().strip())
            if not path.is_file():
                QMessageBox.warning(self, "Astrometria", "FITS invalido.")
                return
            try:
                ra0 = parse_optional_float(self.as_ra0.text())
                dec0 = parse_optional_float(self.as_dec0.text())
                scale = parse_optional_float(self.as_scale.text())
                pa = parse_optional_float(self.as_pa.text())
            except ValueError:
                QMessageBox.warning(
                    self, "Astrometria", "Parametros numericos invalidos."
                )
                return
            store = LocalArtifactStore(self.artifacts_root)
            try:
                uri = self._put_fits(path)
                product = MeasureAstrometry(self.archive, store).execute(
                    workspace_id=ws.id,
                    fits_uri=uri,
                    x=float(self.as_x.value()),
                    y=float(self.as_y.value()),
                    ra0_deg=ra0,
                    dec0_deg=dec0,
                    scale_arcsec=scale,
                    pa_deg=pa if pa is not None else 0.0,
                    designation=self.as_desig.text().strip() or None,
                    band=self.as_band.text().strip() or "R",
                    nonsidereal=self.as_nonsidereal.isChecked(),
                    program_id=self._shell_program_id,
                )
            except (DomainError, ValueError, OSError) as exc:
                QMessageBox.critical(self, "Astrometria", str(exc))
                return
            ra = product.summary.get("ra_deg")
            dec = product.summary.get("dec_deg")
            mag = product.summary.get("mag")
            method = product.parameters.get("method")
            msg = (
                f"product={product.id}  method={method}  "
                f"ra={ra}  dec={dec}  mag={mag}  "
                f"epoch={product.summary.get('epoch_utc')}"
            )
            self.as_result.setText(msg)
            self._append(f"astrometry={product.id}  ra={ra}  dec={dec}  mag={mag}")
            self.cu_product.setText(str(product.id))
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
