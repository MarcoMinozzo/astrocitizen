"""Painel Arquivo: observacoes + produtos + detalhe/plot + abrir/export (U3/U5+)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
from uuid import UUID


def observation_rows(observations: list[dict], *, limit: int = 200) -> list[list[str]]:
    rows: list[list[str]] = []
    for o in observations[:limit]:
        rows.append(
            [
                str(o.get("observed_at_utc", "")),
                "sim" if o.get("simulated") else "real",
                str(o.get("camera_backend") or "-"),
                str(o.get("state") or ""),
                str(o.get("notes") or "")[:40],
                str(o.get("id", ""))[:8],
            ]
        )
    return rows


def product_rows(products: list[Any], *, limit: int = 200) -> list[list[str]]:
    rows: list[list[str]] = []
    for p in products[:limit]:
        summary = getattr(p, "summary", None) or {}
        hint = ""
        if isinstance(summary, dict) and summary:
            parts = [f"{k}={v}" for k, v in list(summary.items())[:3]]
            hint = "; ".join(parts)[:60]
        rows.append(
            [
                str(getattr(p, "product_type", "")),
                str(getattr(p, "state", "")),
                hint,
                str(getattr(p, "id", ""))[:8],
            ]
        )
    return rows


def product_full_ids(products: list[Any], *, limit: int = 200) -> list[str]:
    return [str(getattr(p, "id", "")) for p in products[:limit]]


def build_archive_dashboard() -> type:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QFileDialog,
        QHBoxLayout,
        QInputDialog,
        QLabel,
        QLineEdit,
        QMenu,
        QMessageBox,
        QPushButton,
        QSplitter,
        QTableWidget,
        QTableWidgetItem,
        QTabWidget,
        QTextEdit,
        QToolButton,
        QVBoxLayout,
        QWidget,
    )

    from astrocitizen.adapters.fs import LocalArtifactStore
    from astrocitizen.contribution.aavso import ExportAavso
    from astrocitizen.contribution.bess import annotate_existing_fits
    from astrocitizen.contribution.credentials import LocalCredentialsStore
    from astrocitizen.contribution.exoclock import ExportExoclock
    from astrocitizen.contribution.models import NetworkSubmission
    from astrocitizen.contribution.solar import ExportSolarReport
    from astrocitizen.desktop.plot_widget import build_series_plot
    from astrocitizen.desktop.series import (
        cli_export_hint,
        export_networks_for_type,
        format_product_detail,
        primary_artifact_refs,
        resolve_openable_path,
        series_from_measurement_points,
    )
    from astrocitizen.shared.ids import new_id
    from astrocitizen.shared.paths import default_artifacts_root

    SeriesPlot = build_series_plot()

    class ArchiveDashboard(QWidget):
        def __init__(
            self,
            archive: Any,
            *,
            artifacts_root: Path | None = None,
            on_changed: Any | None = None,
            on_contribute: Callable[..., Any] | None = None,
        ) -> None:
            super().__init__()
            self.archive = archive
            self.artifacts_root = Path(artifacts_root or default_artifacts_root())
            self.on_changed = on_changed
            self.on_contribute = on_contribute
            self._product_ids: list[str] = []
            self.creds = LocalCredentialsStore()

            root = QVBoxLayout(self)
            root.setContentsMargins(16, 12, 16, 12)
            title = QLabel("Arquivo")
            title.setObjectName("pageTitle")
            root.addWidget(title)

            filt = QHBoxLayout()
            self.search = QLineEdit()
            self.search.setPlaceholderText("Filtrar texto...")
            self.search.textChanged.connect(self.reload)
            self.include_sim = QCheckBox("Incluir simulated")
            self.include_sim.setChecked(True)
            self.include_sim.stateChanged.connect(self.reload)
            self.type_filter = QComboBox()
            self.type_filter.addItem("(todos tipos)", None)
            self.type_filter.currentIndexChanged.connect(self.reload)
            btn = QPushButton("Atualizar")
            btn.setObjectName("secondaryBtn")
            btn.clicked.connect(self.reload)
            filt.addWidget(self.search, 1)
            filt.addWidget(self.include_sim)
            filt.addWidget(QLabel("Tipo produto"))
            filt.addWidget(self.type_filter)
            filt.addWidget(btn)
            root.addLayout(filt)

            self.tabs = QTabWidget()
            self.obs_table = QTableWidget(0, 6)
            self.obs_table.setAlternatingRowColors(True)
            self.obs_table.setHorizontalHeaderLabels(
                ["Quando", "Sim", "Backend", "Estado", "Notes", "Id"]
            )
            self.obs_table.horizontalHeader().setStretchLastSection(True)
            self.obs_empty = QLabel()
            self.obs_empty.setObjectName("emptyState")
            self.obs_empty.hide()
            obs_wrap = QWidget()
            ov = QVBoxLayout(obs_wrap)
            ov.setContentsMargins(0, 8, 0, 0)
            ov.addWidget(self.obs_empty)
            ov.addWidget(self.obs_table, 1)
            self.tabs.addTab(obs_wrap, "Observacoes")

            prod_split = QSplitter(Qt.Orientation.Vertical)
            prod_top = QWidget()
            pv = QVBoxLayout(prod_top)
            pv.setContentsMargins(0, 8, 0, 0)
            self.prod_table = QTableWidget(0, 4)
            self.prod_table.setAlternatingRowColors(True)
            self.prod_table.setHorizontalHeaderLabels(
                ["Tipo", "Estado", "Resumo", "Id"]
            )
            self.prod_table.horizontalHeader().setStretchLastSection(True)
            self.prod_table.setSelectionBehavior(
                QTableWidget.SelectionBehavior.SelectRows
            )
            self.prod_table.setSelectionMode(
                QTableWidget.SelectionMode.SingleSelection
            )
            self.prod_table.itemSelectionChanged.connect(self._on_product_selected)
            self.prod_empty = QLabel()
            self.prod_empty.setObjectName("emptyState")
            self.prod_empty.hide()
            pv.addWidget(self.prod_empty)
            pv.addWidget(self.prod_table, 1)

            detail_wrap = QWidget()
            dv = QVBoxLayout(detail_wrap)
            dv.setContentsMargins(0, 0, 0, 0)
            actions = QHBoxLayout()
            self.btn_copy = QPushButton("Copiar UUID")
            self.btn_copy.setObjectName("secondaryBtn")
            self.btn_copy.clicked.connect(self._copy_product_id)
            self.btn_open = QToolButton()
            self.btn_open.setText("Abrir artefacto")
            self.btn_open.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
            self.btn_open.clicked.connect(self._open_artifact)
            open_menu = QMenu(self)
            open_menu.addAction("SO / default", lambda: self._open_artifact_tool("system"))
            open_menu.addAction("DS9", lambda: self._open_artifact_tool("ds9"))
            open_menu.addAction("Siril", lambda: self._open_artifact_tool("siril"))
            open_menu.addAction("ASTAP", lambda: self._open_artifact_tool("astap"))
            self.btn_open.setMenu(open_menu)
            self.btn_export = QToolButton()
            self.btn_export.setText("Exportar")
            self.btn_export.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
            self.btn_export.setObjectName("secondaryBtn")
            self.btn_cli = QPushButton("Ver CLI")
            self.btn_cli.setObjectName("secondaryBtn")
            self.btn_cli.clicked.connect(self._export_hint)
            actions.addWidget(self.btn_copy)
            actions.addWidget(self.btn_open)
            actions.addWidget(self.btn_export)
            actions.addWidget(self.btn_cli)
            actions.addStretch(1)
            dv.addLayout(actions)
            self.detail = QTextEdit()
            self.detail.setReadOnly(True)
            self.detail.setMaximumHeight(120)
            self.detail.setPlaceholderText("Selecione um produto...")
            dv.addWidget(self.detail)
            self.plot = SeriesPlot()
            dv.addWidget(self.plot, 1)

            prod_split.addWidget(prod_top)
            prod_split.addWidget(detail_wrap)
            prod_split.setStretchFactor(0, 2)
            prod_split.setStretchFactor(1, 2)
            self.tabs.addTab(prod_split, "Produtos")
            root.addWidget(self.tabs, 1)

            self.status = QLabel("")
            self.status.setObjectName("emptyState")
            root.addWidget(self.status)
            self._rebuild_export_menu(None)

        def _workspace(self):
            ws = self.archive.list_workspaces()
            return ws[0] if ws else None

        def _fill(
            self,
            table: QTableWidget,
            empty: QLabel,
            rows: list[list[str]],
            module: str,
            *,
            row_ids: list[str] | None = None,
        ) -> None:
            from astrocitizen.desktop.theme import empty_state_text

            table.setRowCount(len(rows))
            for r, row in enumerate(rows):
                for c, val in enumerate(row):
                    item = QTableWidgetItem(val)
                    if row_ids is not None and c == 0 and r < len(row_ids):
                        item.setData(Qt.ItemDataRole.UserRole, row_ids[r])
                    table.setItem(r, c, item)
            if rows:
                empty.hide()
                table.show()
            else:
                empty.setText(empty_state_text(module))
                empty.show()
                table.hide()

        def _selected_product_id(self) -> str | None:
            rows = self.prod_table.selectionModel().selectedRows()
            if not rows:
                return None
            r = rows[0].row()
            item = self.prod_table.item(r, 0)
            if item is None:
                return None
            pid = item.data(Qt.ItemDataRole.UserRole)
            return str(pid) if pid else None

        def _selected_product(self) -> Any | None:
            pid = self._selected_product_id()
            if not pid:
                return None
            try:
                return self.archive.get_analysis_product(UUID(pid))
            except (ValueError, TypeError):
                return None

        def _rebuild_export_menu(self, product: Any | None) -> None:
            menu = QMenu(self)
            ptype = getattr(product, "product_type", None) if product else None
            nets = export_networks_for_type(str(ptype or ""))
            labels = {
                "aavso": "AAVSO Extended",
                "exoclock": "ExoClock CSV",
                "bess": "BeSS FITS",
                "solar": "Relatorio solar",
                "mpc": "Abrir Contribuir (MPC)",
                "tns": "Abrir Contribuir (TNS)",
            }
            direct = {"aavso", "exoclock", "bess", "solar"}
            for net in nets:
                label = labels.get(net, net)
                if net in direct:
                    menu.addAction(
                        label,
                        lambda n=net: self._export_network(n),
                    )
                else:
                    menu.addAction(
                        label,
                        lambda n=net: self._goto_contribute(n),
                    )
            if nets:
                menu.addSeparator()
            menu.addAction(
                "Abrir em Contribuir...",
                lambda: self._goto_contribute(nets[0] if nets else None),
            )
            self.btn_export.setMenu(menu)

        def _on_product_selected(self) -> None:
            pid = self._selected_product_id()
            if not pid:
                self.detail.clear()
                self.plot.clear()
                self._rebuild_export_menu(None)
                return
            try:
                product = self.archive.get_analysis_product(UUID(pid))
            except (ValueError, TypeError):
                product = None
            if product is None:
                self.detail.setPlainText(f"Produto nao encontrado: {pid}")
                self.plot.clear()
                self._rebuild_export_menu(None)
                return
            self._rebuild_export_menu(product)
            points = self.archive.list_measurement_points(UUID(pid))
            self.detail.setPlainText(
                format_product_detail(product, n_points=len(points))
            )
            xs, ys, band = series_from_measurement_points(points)
            if len(xs) >= 2:
                self.plot.set_series(
                    xs,
                    ys,
                    title=f"{product.product_type}  ({len(xs)} pts)",
                    xlabel="x",
                    ylabel=band,
                )
            else:
                self.plot.clear()

        def _copy_product_id(self) -> None:
            pid = self._selected_product_id()
            if not pid:
                QMessageBox.information(self, "Arquivo", "Selecione um produto.")
                return
            QGuiApplication.clipboard().setText(pid)
            self.status.setText(f"UUID copiado: {pid}")

        def _open_artifact(self) -> None:
            self._open_artifact_tool("system")

        def _open_artifact_tool(self, tool_id: str) -> None:
            from astrocitizen.adapters.image_tools import ExternalImageToolLauncher
            from astrocitizen.shared.errors import DomainError

            product = self._selected_product()
            if product is None:
                QMessageBox.information(self, "Arquivo", "Selecione um produto.")
                return
            refs = primary_artifact_refs(product)
            if not refs:
                QMessageBox.information(
                    self, "Arquivo", "Produto sem URI/path de artefacto."
                )
                return
            launcher = ExternalImageToolLauncher()
            last_err = ""
            for label, ref in refs:
                path = resolve_openable_path(ref, store_root=self.artifacts_root)
                if path is None:
                    last_err = f"{label}: nao resolvido ({ref})"
                    continue
                try:
                    ok = launcher.launch(path, tool_id=tool_id)
                except DomainError as exc:
                    last_err = str(exc)
                    continue
                if ok:
                    self.status.setText(f"Aberto ({tool_id}): {label} → {path.name}")
                    return
                last_err = f"{label}: falha ao abrir {path}"
            QMessageBox.warning(
                self,
                "Abrir artefacto",
                last_err or "Nenhum artefacto abrivel.",
            )

        def _goto_contribute(self, network: str | None) -> None:
            pid = self._selected_product_id()
            if not pid:
                QMessageBox.information(self, "Arquivo", "Selecione um produto.")
                return
            if callable(self.on_contribute):
                self.on_contribute(network=network, product_id=pid)
                self.status.setText(f"Contribuir ← {pid[:8]}…")
            else:
                QMessageBox.information(
                    self,
                    "Contribuir",
                    f"Product UUID: {pid}\nRede: {network or '(escolher)'}",
                )

        def _export_hint(self) -> None:
            pid = self._selected_product_id()
            if not pid:
                QMessageBox.information(self, "Arquivo", "Selecione um produto.")
                return
            product = self._selected_product()
            ptype = getattr(product, "product_type", None) if product else None
            QMessageBox.information(
                self, "Ver CLI", cli_export_hint(pid, str(ptype) if ptype else None)
            )

        def _save_submission(
            self,
            *,
            network: str,
            out: Path,
            product_id: UUID,
            summary: dict[str, Any],
        ) -> None:
            ws = self._workspace()
            if ws is None:
                return
            store = LocalArtifactStore(self.artifacts_root)
            uri = store.put(out, key=f"export/{network}/{out.name}")
            sub = NetworkSubmission(
                id=new_id(),
                workspace_id=ws.id,
                network=network,
                status="draft",
                artifact_uri=uri,
                product_id=product_id,
                payload_summary=summary,
            )
            self.archive.save_network_submission(sub)
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(out)))
            self.status.setText(f"Export {network}: {out}")
            if self.on_changed:
                self.on_changed()

        def _export_network(self, network: str) -> None:
            product = self._selected_product()
            if product is None:
                QMessageBox.information(self, "Arquivo", "Selecione um produto.")
                return
            pid = UUID(str(product.id))
            try:
                if network == "aavso":
                    self._export_aavso(pid)
                elif network == "exoclock":
                    self._export_exoclock(pid)
                elif network == "bess":
                    self._export_bess(product, pid)
                elif network == "solar":
                    self._export_solar(pid)
                else:
                    self._goto_contribute(network)
            except Exception as exc:  # noqa: BLE001 - UI boundary
                QMessageBox.critical(self, "Exportar", str(exc))

        def _export_aavso(self, pid: UUID) -> None:
            obscode = self.creds.get_network("aavso").get("obscode") or ""
            star, ok = QInputDialog.getText(self, "AAVSO", "Star name:", text="UNKNOWN")
            if not ok or not star.strip():
                return
            if not obscode:
                obscode, ok = QInputDialog.getText(self, "AAVSO", "OBSCODE:")
                if not ok or not obscode.strip():
                    return
            default = self.artifacts_root / "export" / "aavso" / f"{pid}.txt"
            path, _ = QFileDialog.getSaveFileName(
                self, "Guardar AAVSO", str(default), "Text (*.txt)"
            )
            if not path:
                return
            out = Path(path)
            ExportAavso(self.archive).execute(
                product_id=pid,
                star_name=star.strip(),
                observer_code=str(obscode).strip(),
                out_path=out,
            )
            self._save_submission(
                network="aavso",
                out=out,
                product_id=pid,
                summary={"star": star.strip(), "note": "Arquivo GUI"},
            )

        def _export_exoclock(self, pid: UUID) -> None:
            target, ok = QInputDialog.getText(
                self, "ExoClock", "Target:", text="TARGET"
            )
            if not ok or not target.strip():
                return
            observer = self.creds.get_network("exoclock").get("observer") or "AstroCitizen"
            default = self.artifacts_root / "export" / "exoclock" / f"{pid}.txt"
            path, _ = QFileDialog.getSaveFileName(
                self, "Guardar ExoClock", str(default), "Text (*.txt *.csv)"
            )
            if not path:
                return
            out = Path(path)
            ExportExoclock(self.archive).execute(
                product_id=pid,
                target=target.strip(),
                out_path=out,
                observer=str(observer),
            )
            self._save_submission(
                network="exoclock",
                out=out,
                product_id=pid,
                summary={"target": target.strip()},
            )

        def _export_bess(self, product: Any, pid: UUID) -> None:
            refs = primary_artifact_refs(product)
            spectrum = None
            for label, ref in refs:
                if label in ("spectrum_uri", "fits_uri"):
                    spectrum = resolve_openable_path(
                        ref, store_root=self.artifacts_root
                    )
                    if spectrum is not None and spectrum.is_file():
                        break
            if spectrum is None:
                QMessageBox.warning(
                    self, "BeSS", "Produto sem spectrum_uri/fits resolvivel."
                )
                return
            observer = (
                self.creds.get_network("bess").get("observer") or "AstroCitizen"
            )
            default = self.artifacts_root / "export" / "bess" / f"{pid}.fits"
            path, _ = QFileDialog.getSaveFileName(
                self, "Guardar BeSS FITS", str(default), "FITS (*.fits)"
            )
            if not path:
                return
            out = Path(path)
            annotate_existing_fits(
                spectrum, out, observer=str(observer)
            )
            self._save_submission(
                network="bess",
                out=out,
                product_id=pid,
                summary={"note": "annotate from Arquivo"},
            )

        def _export_solar(self, pid: UUID) -> None:
            default = self.artifacts_root / "export" / "solar" / f"{pid}.txt"
            path, _ = QFileDialog.getSaveFileName(
                self, "Guardar relatorio solar", str(default), "Text (*.txt)"
            )
            if not path:
                return
            out = Path(path)
            ExportSolarReport(self.archive).execute(product_id=pid, out_path=out)
            self._save_submission(
                network="solar",
                out=out,
                product_id=pid,
                summary={"note": "Arquivo GUI"},
            )

        def reload(self) -> None:
            ws = self._workspace()
            if ws is None:
                return
            q = self.search.text().strip().lower()
            obs = self.archive.list_observations(
                ws.id, include_simulated=self.include_sim.isChecked()
            )
            if q:
                obs = [
                    o
                    for o in obs
                    if q in str(o.get("id", "")).lower()
                    or q in str(o.get("notes", "")).lower()
                    or q in str(o.get("observed_at_utc", "")).lower()
                    or q in str(o.get("camera_backend", "")).lower()
                ]
            self._fill(
                self.obs_table,
                self.obs_empty,
                observation_rows(obs),
                "Arquivo",
            )

            products = self.archive.list_analysis_products(ws.id, limit=500)
            types = sorted({p.product_type for p in products})
            cur_type = self.type_filter.currentData()
            self.type_filter.blockSignals(True)
            self.type_filter.clear()
            self.type_filter.addItem("(todos tipos)", None)
            for t in types:
                self.type_filter.addItem(t, t)
            if cur_type is not None:
                i = self.type_filter.findData(cur_type)
                if i >= 0:
                    self.type_filter.setCurrentIndex(i)
            self.type_filter.blockSignals(False)
            ptype = self.type_filter.currentData()
            if ptype:
                products = [p for p in products if p.product_type == ptype]
            if q:
                products = [
                    p
                    for p in products
                    if q in str(p.id).lower()
                    or q in p.product_type.lower()
                    or q in str(p.summary).lower()
                ]
            limited = products[:200]
            self._product_ids = product_full_ids(limited, limit=200)
            self._fill(
                self.prod_table,
                self.prod_empty,
                product_rows(limited, limit=200),
                "Arquivo",
                row_ids=self._product_ids,
            )
            self.status.setText(
                f"{len(obs)} observacoes · {len(products)} produtos (filtro aplicado)"
            )
            if self.prod_table.rowCount() == 0:
                self.detail.clear()
                self.plot.clear()
                self._rebuild_export_menu(None)

    return ArchiveDashboard
