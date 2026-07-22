"""CRUD GUI: Equipamento + ConfiguracaoInstrumental (AC-072 / AC-021)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import UUID


def build_equipment_page() -> type:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QDialog,
        QDialogButtonBox,
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

    from astrocitizen.inventory.models import Equipment, InstrumentConfig
    from astrocitizen.shared.ids import new_id

    EQ_TYPES = ("camera", "mount", "focuser", "filter_wheel", "spectrograph", "other")
    BACKENDS = ("sim", "alpaca", "udrv", "")

    class EquipmentDialog(QDialog):
        def __init__(
            self, parent: QWidget | None = None, eq: Equipment | None = None
        ) -> None:
            super().__init__(parent)
            self.setWindowTitle("Editar equipamento" if eq else "Novo equipamento")
            self._eq = eq
            form = QFormLayout(self)
            self.type = QComboBox()
            for t in EQ_TYPES:
                self.type.addItem(t, t)
            if eq:
                i = self.type.findData(eq.type)
                if i >= 0:
                    self.type.setCurrentIndex(i)
            self.name = QLineEdit(eq.name if eq else "")
            self.backend = QComboBox()
            for b in BACKENDS:
                self.backend.addItem(b or "(nenhum)", b or None)
            if eq and eq.backend:
                i = self.backend.findData(eq.backend)
                if i >= 0:
                    self.backend.setCurrentIndex(i)
            self.available = QCheckBox("Disponivel")
            self.available.setChecked(True if eq is None else bool(eq.available))
            form.addRow("Tipo", self.type)
            form.addRow("Nome", self.name)
            form.addRow("Backend", self.backend)
            form.addRow(self.available)
            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )
            buttons.accepted.connect(self.accept)
            buttons.rejected.connect(self.reject)
            form.addRow(buttons)

        def build(self, workspace_id: UUID) -> Equipment:
            name = self.name.text().strip()
            if not name:
                raise ValueError("Nome obrigatorio")
            base = self._eq
            return Equipment(
                id=base.id if base else new_id(),
                workspace_id=workspace_id,
                type=str(self.type.currentData()),
                name=name,
                backend=self.backend.currentData(),
                available=self.available.isChecked(),
                metadata=dict(base.metadata) if base else {},
                version=base.version if base else 1,
            )

    class ConfigDialog(QDialog):
        def __init__(
            self,
            archive: Any,
            workspace_id: UUID,
            parent: QWidget | None = None,
            config: InstrumentConfig | None = None,
        ) -> None:
            super().__init__(parent)
            self.setWindowTitle("Editar setup" if config else "Novo setup")
            self._config = config
            self._workspace_id = workspace_id
            eqs = archive.list_equipment(workspace_id)
            form = QFormLayout(self)
            self.name = QLineEdit(config.name if config else "Setup principal")
            self.notes = QLineEdit(config.notes if config else "")
            self.camera = QComboBox()
            self.mount = QComboBox()
            self.focuser = QComboBox()
            for combo, role in (
                (self.camera, "camera"),
                (self.mount, "mount"),
                (self.focuser, "focuser"),
            ):
                combo.addItem("(nenhum)", None)
                for e in eqs:
                    if e.type == role or (role == "camera" and e.type == "spectrograph"):
                        combo.addItem(f"{e.name} [{e.backend or '-'}]", e.id)
                if config and role in config.items:
                    i = combo.findData(config.items[role])
                    if i >= 0:
                        combo.setCurrentIndex(i)
            form.addRow("Nome do setup", self.name)
            form.addRow("Notas", self.notes)
            form.addRow("Camera", self.camera)
            form.addRow("Montagem", self.mount)
            form.addRow("Focuser", self.focuser)
            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )
            buttons.accepted.connect(self.accept)
            buttons.rejected.connect(self.reject)
            form.addRow(buttons)

        def build(self) -> InstrumentConfig:
            name = self.name.text().strip()
            if not name:
                raise ValueError("Nome do setup obrigatorio")
            items: dict[str, UUID] = {}
            for role, combo in (
                ("camera", self.camera),
                ("mount", self.mount),
                ("focuser", self.focuser),
            ):
                eid = combo.currentData()
                if eid is not None:
                    items[role] = eid
            if not items:
                raise ValueError("Escolha pelo menos um equipamento")
            base = self._config
            return InstrumentConfig(
                id=base.id if base else new_id(),
                workspace_id=self._workspace_id,
                name=name,
                notes=self.notes.text().strip(),
                items=items,
                version=base.version if base else 1,
            )

    class AssignProgramDialog(QDialog):
        def __init__(self, archive: Any, workspace_id: UUID, parent: QWidget | None = None) -> None:
            super().__init__(parent)
            self.setWindowTitle("Atribuir setup a programa")
            form = QFormLayout(self)
            self.program = QComboBox()
            for p in archive.list_programs(workspace_id):
                self.program.addItem(f"{p.template_id} · {p.name}", p.id)
            self.config = QComboBox()
            for c in archive.list_instrument_configs(workspace_id):
                roles = ",".join(sorted(c.items.keys())) or "-"
                self.config.addItem(f"{c.name} ({roles})", c.id)
            form.addRow("Programa", self.program)
            form.addRow("Setup", self.config)
            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )
            buttons.accepted.connect(self.accept)
            buttons.rejected.connect(self.reject)
            form.addRow(buttons)

        def selection(self) -> tuple[UUID, UUID]:
            pid = self.program.currentData()
            cid = self.config.currentData()
            if pid is None or cid is None:
                raise ValueError("Programa e setup obrigatorios")
            return pid, cid

    class EquipmentPage(QWidget):
        def __init__(
            self,
            archive: Any,
            *,
            on_changed: Callable[[], None] | None = None,
        ) -> None:
            super().__init__()
            self.archive = archive
            self.on_changed = on_changed
            self._eq_ids: list[UUID] = []
            self._cfg_ids: list[UUID] = []

            lay = QVBoxLayout(self)
            lay.setContentsMargins(16, 12, 16, 12)

            self.title = QLabel("Equipamento")
            self.title.setObjectName("pageTitle")
            lay.addWidget(self.title)

            eq_bar = QHBoxLayout()
            self.btn_eq_new = QPushButton("Novo equipamento")
            self.btn_eq_edit = QPushButton("Editar")
            self.btn_eq_del = QPushButton("Remover")
            self.btn_refresh = QPushButton("Atualizar")
            for b in (self.btn_eq_new, self.btn_eq_edit, self.btn_eq_del, self.btn_refresh):
                eq_bar.addWidget(b)
            eq_bar.addStretch(1)
            lay.addLayout(eq_bar)

            self.eq_empty = QLabel()
            self.eq_empty.setObjectName("emptyState")
            self.eq_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.eq_empty.hide()
            self.eq_table = QTableWidget(0, 4)
            self.eq_table.setAlternatingRowColors(True)
            self.eq_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            self.eq_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
            self.eq_table.horizontalHeader().setStretchLastSection(True)
            self.eq_table.setHorizontalHeaderLabels(["Tipo", "Nome", "Backend", "OK"])
            lay.addWidget(self.eq_empty)
            lay.addWidget(self.eq_table, 1)

            cfg_title = QLabel("Setups instrumentais")
            cfg_title.setObjectName("pageTitle")
            lay.addWidget(cfg_title)
            cfg_bar = QHBoxLayout()
            self.btn_cfg_new = QPushButton("Novo setup")
            self.btn_cfg_edit = QPushButton("Editar setup")
            self.btn_assign = QPushButton("Atribuir a programa")
            for b in (self.btn_cfg_new, self.btn_cfg_edit, self.btn_assign):
                cfg_bar.addWidget(b)
            cfg_bar.addStretch(1)
            lay.addLayout(cfg_bar)

            self.cfg_empty = QLabel()
            self.cfg_empty.setObjectName("emptyState")
            self.cfg_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.cfg_empty.hide()
            self.cfg_table = QTableWidget(0, 3)
            self.cfg_table.setAlternatingRowColors(True)
            self.cfg_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            self.cfg_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
            self.cfg_table.horizontalHeader().setStretchLastSection(True)
            self.cfg_table.setHorizontalHeaderLabels(["Nome", "Papeis", "Notas"])
            lay.addWidget(self.cfg_empty)
            lay.addWidget(self.cfg_table, 1)

            self.btn_eq_new.clicked.connect(self._eq_new)
            self.btn_eq_edit.clicked.connect(self._eq_edit)
            self.btn_eq_del.clicked.connect(self._eq_del)
            self.btn_refresh.clicked.connect(self.reload)
            self.btn_cfg_new.clicked.connect(self._cfg_new)
            self.btn_cfg_edit.clicked.connect(self._cfg_edit)
            self.btn_assign.clicked.connect(self._assign)

        def _workspace(self):
            ws = self.archive.list_workspaces()
            return ws[0] if ws else None

        def reload(self) -> None:
            ws = self._workspace()
            eqs = self.archive.list_equipment(ws.id) if ws else []
            cfgs = self.archive.list_instrument_configs(ws.id) if ws else []
            self._eq_ids = [e.id for e in eqs]
            self._cfg_ids = [c.id for c in cfgs]
            self.title.setText(f"Equipamento ({len(eqs)}) · setups ({len(cfgs)})")

            self.eq_table.setRowCount(len(eqs))
            for r, e in enumerate(eqs):
                vals = [e.type, e.name, e.backend or "-", "sim" if e.available else "nao"]
                for c, v in enumerate(vals):
                    self.eq_table.setItem(r, c, QTableWidgetItem(v))
            if eqs:
                self.eq_empty.hide()
                self.eq_table.show()
            else:
                self.eq_empty.setText("Nenhum equipamento. Use Novo (camera/mount/focuser).")
                self.eq_empty.show()
                self.eq_table.hide()

            self.cfg_table.setRowCount(len(cfgs))
            for r, c in enumerate(cfgs):
                roles = ",".join(sorted(c.items.keys())) or "-"
                for col, v in enumerate([c.name, roles, c.notes or "-"]):
                    self.cfg_table.setItem(r, col, QTableWidgetItem(v))
            if cfgs:
                self.cfg_empty.hide()
                self.cfg_table.show()
            else:
                self.cfg_empty.setText(
                    "Nenhum setup. Crie equipamento e depois Novo setup."
                )
                self.cfg_empty.show()
                self.cfg_table.hide()

        def _selected_eq(self) -> UUID | None:
            rows = self.eq_table.selectionModel().selectedRows()
            if not rows:
                return None
            i = rows[0].row()
            return self._eq_ids[i] if 0 <= i < len(self._eq_ids) else None

        def _selected_cfg(self) -> UUID | None:
            rows = self.cfg_table.selectionModel().selectedRows()
            if not rows:
                return None
            i = rows[0].row()
            return self._cfg_ids[i] if 0 <= i < len(self._cfg_ids) else None

        def _notify(self) -> None:
            self.reload()
            if self.on_changed:
                self.on_changed()

        def _eq_new(self) -> None:
            ws = self._workspace()
            if ws is None:
                return
            dlg = EquipmentDialog(self)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
            try:
                self.archive.upsert_equipment(dlg.build(ws.id))
            except ValueError as e:
                QMessageBox.warning(self, "Equipamento", str(e))
                return
            self._notify()

        def _eq_edit(self) -> None:
            eid = self._selected_eq()
            ws = self._workspace()
            if eid is None or ws is None:
                QMessageBox.information(self, "Equipamento", "Selecione um equipamento.")
                return
            eq = self.archive.get_equipment(eid)
            if eq is None:
                return
            dlg = EquipmentDialog(self, eq)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
            try:
                self.archive.upsert_equipment(dlg.build(ws.id))
            except ValueError as e:
                QMessageBox.warning(self, "Equipamento", str(e))
                return
            self._notify()

        def _eq_del(self) -> None:
            eid = self._selected_eq()
            if eid is None:
                QMessageBox.information(self, "Equipamento", "Selecione um equipamento.")
                return
            eq = self.archive.get_equipment(eid)
            name = eq.name if eq else str(eid)[:8]
            if (
                QMessageBox.question(self, "Remover", f"Remover '{name}'?")
                != QMessageBox.StandardButton.Yes
            ):
                return
            self.archive.soft_delete_equipment(eid)
            self._notify()

        def _cfg_new(self) -> None:
            ws = self._workspace()
            if ws is None:
                return
            if not self.archive.list_equipment(ws.id):
                QMessageBox.information(
                    self, "Setup", "Crie equipamento antes do setup."
                )
                return
            dlg = ConfigDialog(self.archive, ws.id, self)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
            try:
                self.archive.upsert_instrument_config(dlg.build())
            except ValueError as e:
                QMessageBox.warning(self, "Setup", str(e))
                return
            self._notify()

        def _cfg_edit(self) -> None:
            cid = self._selected_cfg()
            ws = self._workspace()
            if cid is None or ws is None:
                QMessageBox.information(self, "Setup", "Selecione um setup.")
                return
            cfg = self.archive.get_instrument_config(cid)
            if cfg is None:
                return
            dlg = ConfigDialog(self.archive, ws.id, self, cfg)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
            try:
                self.archive.upsert_instrument_config(dlg.build())
            except ValueError as e:
                QMessageBox.warning(self, "Setup", str(e))
                return
            self._notify()

        def _assign(self) -> None:
            ws = self._workspace()
            if ws is None:
                return
            if not self.archive.list_programs(ws.id):
                QMessageBox.information(self, "Setup", "Crie um programa primeiro.")
                return
            if not self.archive.list_instrument_configs(ws.id):
                QMessageBox.information(self, "Setup", "Crie um setup primeiro.")
                return
            dlg = AssignProgramDialog(self.archive, ws.id, self)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
            try:
                pid, cid = dlg.selection()
            except ValueError as e:
                QMessageBox.warning(self, "Setup", str(e))
                return
            prog = self.archive.get_program(pid)
            if prog is None:
                return
            prog.default_instrument_config_id = cid
            self.archive.upsert_program(prog)
            QMessageBox.information(
                self,
                "Setup",
                f"Programa '{prog.name}' usa agora o setup seleccionado.",
            )
            self._notify()

    return EquipmentPage
