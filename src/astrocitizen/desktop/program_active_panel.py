"""Painel Programa activo: alvos, passos workflow, atalho Contribuir."""

from __future__ import annotations

from typing import Any, Callable
from uuid import UUID


def build_program_active_dashboard() -> type:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QComboBox,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QMessageBox,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )

    from astrocitizen.programs.guide import (
        normalize_network_key,
        resolve_export_networks,
        step_nav_rows,
        target_link_rows,
    )
    from astrocitizen.programs.workflows import workflow_for

    class ProgramActiveDashboard(QWidget):
        def __init__(
            self,
            archive: Any,
            *,
            on_navigate: Callable[..., None] | None = None,
            on_changed: Callable[[], None] | None = None,
        ) -> None:
            super().__init__()
            self.archive = archive
            self.on_navigate = on_navigate
            self.on_changed = on_changed
            self._shell_program_id: UUID | None = None
            self._step_navs: list[dict[str, str]] = []
            self._network_keys: list[str] = []

            root = QVBoxLayout(self)
            root.setContentsMargins(16, 12, 16, 12)
            title = QLabel("Programa activo")
            title.setObjectName("pageTitle")
            root.addWidget(title)
            hint = QLabel(
                "Campanha seleccionada na ContextBar: alvos ligados, "
                "passos do template PO-* e atalho para Contribuir."
            )
            hint.setObjectName("emptyState")
            hint.setWordWrap(True)
            hint.setStyleSheet("padding: 0 0 8px 0;")
            root.addWidget(hint)

            self.summary = QLabel("Seleccione um programa na barra de contexto.")
            self.summary.setObjectName("emptyState")
            self.summary.setWordWrap(True)
            root.addWidget(self.summary)

            root.addWidget(QLabel("Alvos ligados"))
            self.targets = QTableWidget(0, 4)
            self.targets.setAlternatingRowColors(True)
            self.targets.setHorizontalHeaderLabels(
                ["Designacao", "Papel", "Tipo", "Id"]
            )
            self.targets.horizontalHeader().setStretchLastSection(True)
            self.targets.setMaximumHeight(160)
            root.addWidget(self.targets)

            link_row = QHBoxLayout()
            self.link_combo = QComboBox()
            self.link_role = QComboBox()
            for role in ("primary", "comp", "check"):
                self.link_role.addItem(role, role)
            btn_link = QPushButton("Ligar alvo")
            btn_link.clicked.connect(self._link_target)
            link_row.addWidget(self.link_combo, 1)
            link_row.addWidget(self.link_role)
            link_row.addWidget(btn_link)
            root.addLayout(link_row)

            root.addWidget(QLabel("Passos do workflow"))
            self.steps = QListWidget()
            self.steps.itemDoubleClicked.connect(self._goto_step_item)
            root.addWidget(self.steps, 1)
            step_btns = QHBoxLayout()
            btn_step = QPushButton("Ir ao passo")
            btn_step.clicked.connect(self._goto_selected_step)
            step_btns.addWidget(btn_step)
            step_btns.addStretch(1)
            root.addLayout(step_btns)

            root.addWidget(QLabel("Redes / Contribuir"))
            net_row = QHBoxLayout()
            self.net_combo = QComboBox()
            btn_net = QPushButton("Abrir Contribuir")
            btn_net.clicked.connect(self._open_contribute)
            net_row.addWidget(self.net_combo, 1)
            net_row.addWidget(btn_net)
            root.addLayout(net_row)

            self.products = QLabel("")
            self.products.setObjectName("emptyState")
            self.products.setWordWrap(True)
            root.addWidget(self.products)

            btn_reload = QPushButton("Atualizar")
            btn_reload.setObjectName("secondaryBtn")
            btn_reload.clicked.connect(self.reload)
            root.addWidget(btn_reload)

        def _workspace(self):
            ws = self.archive.list_workspaces()
            return ws[0] if ws else None

        def set_shell_context(
            self, *, site_id: object = None, program_id: object = None
        ) -> None:
            self._shell_program_id = program_id if program_id else None
            self.reload()

        def reload(self) -> None:
            ws = self._workspace()
            self.link_combo.clear()
            self.net_combo.clear()
            self.steps.clear()
            self._step_navs = []
            self._network_keys = []
            self.targets.setRowCount(0)

            if ws is None or self._shell_program_id is None:
                self.summary.setText(
                    "Nenhum programa na ContextBar. "
                    "Crie em Configurar → Programas e seleccione acima."
                )
                self.products.setText("")
                return

            program = self.archive.get_program(self._shell_program_id)
            if program is None:
                self.summary.setText("Programa nao encontrado.")
                self.products.setText("")
                return

            template = self.archive.get_program_template(program.template_id)
            wf = workflow_for(program.template_id)
            tmpl_name = template.name if template else program.template_id
            wf_name = (wf or {}).get("name") or "(sem workflow)"
            self.summary.setText(
                f"{program.template_id} · {program.name}\n"
                f"estado={program.state}  prioridade={program.priority}\n"
                f"template={tmpl_name}\n"
                f"workflow={wf_name}"
            )

            links = self.archive.list_program_targets(program.id)
            rows = target_link_rows(links)
            self.targets.setRowCount(len(rows))
            for r, row in enumerate(rows):
                for c, val in enumerate(row):
                    self.targets.setItem(r, c, QTableWidgetItem(val))

            linked_ids = {t.id for t, _role, _o in links}
            for t in self.archive.list_targets(ws.id):
                if t.id in linked_ids:
                    continue
                self.link_combo.addItem(t.designation, t.id)
            if self.link_combo.count() == 0:
                self.link_combo.addItem("(sem alvos livres)", None)

            self._step_navs = step_nav_rows(wf)
            for nav in self._step_navs:
                label = nav.get("label") or nav["step"]
                area = nav.get("area", "")
                item = QListWidgetItem(f"{nav['step']}  →  {label} ({area})")
                item.setData(Qt.ItemDataRole.UserRole, nav)
                self.steps.addItem(item)

            nets = resolve_export_networks(program, wf, template)
            for n in nets:
                key = normalize_network_key(n)
                self.net_combo.addItem(n, key)
                if key:
                    self._network_keys.append(key)
            if self.net_combo.count() == 0:
                self.net_combo.addItem("(sem rede mapeada)", None)

            products = [
                p
                for p in self.archive.list_analysis_products(ws.id, limit=80)
                if p.program_id == program.id
            ]
            if products:
                bits = [
                    f"{p.product_type}:{str(p.id)[:8]}" for p in products[:8]
                ]
                self.products.setText(
                    f"{len(products)} produtos deste programa — "
                    + "; ".join(bits)
                )
            else:
                self.products.setText(
                    "Ainda sem produtos com este program_id "
                    "(observe/analise com o programa na ContextBar)."
                )

        def _link_target(self) -> None:
            if self._shell_program_id is None:
                QMessageBox.information(
                    self, "Programa", "Seleccione um programa na ContextBar."
                )
                return
            tid = self.link_combo.currentData()
            if tid is None:
                QMessageBox.information(
                    self, "Programa", "Crie alvos em Configurar → Alvos."
                )
                return
            role = str(self.link_role.currentData() or "primary")
            self.archive.link_program_target(
                self._shell_program_id, tid, role=role
            )
            self.reload()
            if self.on_changed:
                self.on_changed()

        def _goto_selected_step(self) -> None:
            item = self.steps.currentItem()
            if item is None:
                QMessageBox.information(self, "Programa", "Escolha um passo.")
                return
            self._goto_step_item(item)

        def _goto_step_item(self, item: QListWidgetItem) -> None:
            nav = item.data(Qt.ItemDataRole.UserRole)
            if not isinstance(nav, dict) or not self.on_navigate:
                return
            self.on_navigate(
                nav.get("area"),
                hub_tab=nav.get("hub_tab"),
                analyze_tab=nav.get("analyze_tab"),
                network=nav.get("network"),
            )

        def _open_contribute(self) -> None:
            if not self.on_navigate:
                return
            key = self.net_combo.currentData()
            self.on_navigate("Contribuir", network=key)

    return ProgramActiveDashboard
