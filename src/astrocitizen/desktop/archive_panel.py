"""Painel Arquivo: observacoes + produtos de analise (U3)."""

from __future__ import annotations

from typing import Any


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
            # first few summary values
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


def build_archive_dashboard() -> type:
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )

    class ArchiveDashboard(QWidget):
        def __init__(self, archive: Any, *, on_changed: Any | None = None) -> None:
            super().__init__()
            self.archive = archive
            self.on_changed = on_changed

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

            self.prod_table = QTableWidget(0, 4)
            self.prod_table.setAlternatingRowColors(True)
            self.prod_table.setHorizontalHeaderLabels(
                ["Tipo", "Estado", "Resumo", "Id"]
            )
            self.prod_table.horizontalHeader().setStretchLastSection(True)
            self.prod_empty = QLabel()
            self.prod_empty.setObjectName("emptyState")
            self.prod_empty.hide()
            prod_wrap = QWidget()
            pv = QVBoxLayout(prod_wrap)
            pv.setContentsMargins(0, 8, 0, 0)
            pv.addWidget(self.prod_empty)
            pv.addWidget(self.prod_table, 1)
            self.tabs.addTab(prod_wrap, "Produtos")
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
        ) -> None:
            from astrocitizen.desktop.theme import empty_state_text

            table.setRowCount(len(rows))
            for r, row in enumerate(rows):
                for c, val in enumerate(row):
                    table.setItem(r, c, QTableWidgetItem(val))
            if rows:
                empty.hide()
                table.show()
            else:
                empty.setText(empty_state_text(module))
                empty.show()
                table.hide()

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
            self._fill(
                self.prod_table,
                self.prod_empty,
                product_rows(products),
                "Arquivo",
            )
            self.status.setText(
                f"{len(obs)} observacoes · {len(products)} produtos (filtro aplicado)"
            )

    return ArchiveDashboard
