"""Painel Arquivo: observacoes + produtos + detalhe/plot (U3/U5)."""

from __future__ import annotations

from typing import Any
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
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMessageBox,
        QPushButton,
        QSplitter,
        QTableWidget,
        QTableWidgetItem,
        QTabWidget,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    from astrocitizen.desktop.plot_widget import build_series_plot
    from astrocitizen.desktop.series import (
        format_product_detail,
        series_from_measurement_points,
    )

    SeriesPlot = build_series_plot()

    class ArchiveDashboard(QWidget):
        def __init__(self, archive: Any, *, on_changed: Any | None = None) -> None:
            super().__init__()
            self.archive = archive
            self.on_changed = on_changed
            self._product_ids: list[str] = []

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
            self.btn_export = QPushButton("Hint export")
            self.btn_export.setObjectName("secondaryBtn")
            self.btn_export.clicked.connect(self._export_hint)
            actions.addWidget(self.btn_copy)
            actions.addWidget(self.btn_export)
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

        def _on_product_selected(self) -> None:
            pid = self._selected_product_id()
            if not pid:
                self.detail.clear()
                self.plot.clear()
                return
            try:
                product = self.archive.get_analysis_product(UUID(pid))
            except (ValueError, TypeError):
                product = None
            if product is None:
                self.detail.setPlainText(f"Produto nao encontrado: {pid}")
                self.plot.clear()
                return
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

        def _export_hint(self) -> None:
            pid = self._selected_product_id()
            if not pid:
                QMessageBox.information(self, "Arquivo", "Selecione um produto.")
                return
            tip = (
                "Export / contribuicao via CLI (espelho da GUI):\n\n"
                f"  astrocitizen contribute aavso --product {pid} "
                "--star NAME --out ./aavso.txt\n"
                f"  astrocitizen contribute exoclock --product {pid} --out ./exo.csv\n"
                f"  astrocitizen contribute solar --product {pid} --out ./solar/\n\n"
                "Ajuste a rede e flags (--star, --out, ...) conforme o tipo."
            )
            QMessageBox.information(self, "Hint export", tip)

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

    return ArchiveDashboard
