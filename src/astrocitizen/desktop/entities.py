"""CRUD GUI: Sites, Programas, Alvos (AC-072 evolucao)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import UUID


def build_sites_page() -> type:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QCheckBox,
        QDialog,
        QDialogButtonBox,
        QDoubleSpinBox,
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

    from astrocitizen.inventory.models import Site
    from astrocitizen.shared.ids import new_id

    class SiteDialog(QDialog):
        def __init__(self, parent: QWidget | None = None, site: Site | None = None) -> None:
            super().__init__(parent)
            self.setWindowTitle("Editar site" if site else "Novo site")
            self._site = site
            form = QFormLayout(self)
            self.name = QLineEdit(site.name if site else "")
            self.lat = QDoubleSpinBox()
            self.lat.setRange(-90, 90)
            self.lat.setDecimals(6)
            self.lat.setValue(site.latitude_deg if site else -23.55)
            self.lon = QDoubleSpinBox()
            self.lon.setRange(-180, 180)
            self.lon.setDecimals(6)
            self.lon.setValue(site.longitude_deg if site else -46.63)
            self.elev = QDoubleSpinBox()
            self.elev.setRange(-500, 9000)
            self.elev.setDecimals(1)
            self.elev.setValue(site.elevation_m if site else 760.0)
            self.tz = QLineEdit(site.timezone if site else "America/Sao_Paulo")
            self.min_alt = QDoubleSpinBox()
            self.min_alt.setRange(0, 90)
            self.min_alt.setValue(site.min_altitude_deg if site else 25.0)
            self.is_default = QCheckBox("Site predefinido")
            self.is_default.setChecked(bool(site.is_default) if site else False)
            form.addRow("Nome", self.name)
            form.addRow("Latitude", self.lat)
            form.addRow("Longitude", self.lon)
            form.addRow("Elevacao (m)", self.elev)
            form.addRow("Timezone", self.tz)
            form.addRow("Alt. min (deg)", self.min_alt)
            form.addRow(self.is_default)
            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )
            buttons.accepted.connect(self.accept)
            buttons.rejected.connect(self.reject)
            form.addRow(buttons)

        def build(self, workspace_id: UUID) -> Site:
            name = self.name.text().strip()
            if not name:
                raise ValueError("Nome obrigatorio")
            base = self._site
            return Site(
                id=base.id if base else new_id(),
                workspace_id=workspace_id,
                name=name,
                latitude_deg=float(self.lat.value()),
                longitude_deg=float(self.lon.value()),
                elevation_m=float(self.elev.value()),
                timezone=self.tz.text().strip() or "UTC",
                min_altitude_deg=float(self.min_alt.value()),
                night_start_rule=base.night_start_rule if base else "astronomical_twilight",
                meteo_thresholds=dict(base.meteo_thresholds) if base else {},
                is_default=self.is_default.isChecked(),
                version=base.version if base else 1,
            )

    class SitesPage(QWidget):
        def __init__(
            self,
            archive: Any,
            *,
            on_changed: Callable[[], None] | None = None,
        ) -> None:
            super().__init__()
            self.archive = archive
            self.on_changed = on_changed
            self._ids: list[UUID] = []
            lay = QVBoxLayout(self)
            lay.setContentsMargins(16, 12, 16, 12)
            self.title = QLabel("Sites")
            self.title.setObjectName("pageTitle")
            bar = QHBoxLayout()
            self.btn_new = QPushButton("Novo")
            self.btn_edit = QPushButton("Editar")
            self.btn_del = QPushButton("Remover")
            self.btn_refresh = QPushButton("Atualizar")
            for b in (self.btn_new, self.btn_edit, self.btn_del, self.btn_refresh):
                bar.addWidget(b)
            bar.addStretch(1)
            self.empty = QLabel()
            self.empty.setObjectName("emptyState")
            self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.empty.hide()
            self.table = QTableWidget(0, 5)
            self.table.setAlternatingRowColors(True)
            self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
            self.table.horizontalHeader().setStretchLastSection(True)
            self.table.setHorizontalHeaderLabels(["Nome", "Lat", "Lon", "TZ", "Default"])
            lay.addWidget(self.title)
            lay.addLayout(bar)
            lay.addWidget(self.empty)
            lay.addWidget(self.table, 1)
            self.btn_new.clicked.connect(self._new)
            self.btn_edit.clicked.connect(self._edit)
            self.btn_del.clicked.connect(self._delete)
            self.btn_refresh.clicked.connect(self.reload)

        def _workspace(self):
            ws = self.archive.list_workspaces()
            return ws[0] if ws else None

        def reload(self) -> None:
            ws = self._workspace()
            sites = self.archive.list_sites(ws.id) if ws else []
            self._ids = [s.id for s in sites]
            self.title.setText(f"Sites ({len(sites)})")
            self.table.setRowCount(len(sites))
            for r, s in enumerate(sites):
                vals = [
                    s.name,
                    f"{s.latitude_deg:.4f}",
                    f"{s.longitude_deg:.4f}",
                    s.timezone,
                    "sim" if s.is_default else "",
                ]
                for c, v in enumerate(vals):
                    self.table.setItem(r, c, QTableWidgetItem(v))
            if sites:
                self.empty.hide()
                self.table.show()
            else:
                self.empty.setText("Nenhum site. Use Novo ou CLI: astrocitizen site add")
                self.empty.show()
                self.table.hide()

        def _selected_id(self) -> UUID | None:
            rows = self.table.selectionModel().selectedRows()
            if not rows:
                return None
            i = rows[0].row()
            if 0 <= i < len(self._ids):
                return self._ids[i]
            return None

        def _new(self) -> None:
            ws = self._workspace()
            if ws is None:
                QMessageBox.warning(self, "Sites", "Sem workspace.")
                return
            dlg = SiteDialog(self)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
            try:
                site = dlg.build(ws.id)
            except ValueError as e:
                QMessageBox.warning(self, "Sites", str(e))
                return
            self.archive.upsert_site(site)
            self.reload()
            if self.on_changed:
                self.on_changed()

        def _edit(self) -> None:
            sid = self._selected_id()
            ws = self._workspace()
            if sid is None or ws is None:
                QMessageBox.information(self, "Sites", "Selecione um site.")
                return
            site = self.archive.get_site(sid)
            if site is None:
                return
            dlg = SiteDialog(self, site)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
            try:
                updated = dlg.build(ws.id)
            except ValueError as e:
                QMessageBox.warning(self, "Sites", str(e))
                return
            self.archive.upsert_site(updated)
            self.reload()
            if self.on_changed:
                self.on_changed()

        def _delete(self) -> None:
            sid = self._selected_id()
            if sid is None:
                QMessageBox.information(self, "Sites", "Selecione um site.")
                return
            site = self.archive.get_site(sid)
            name = site.name if site else str(sid)[:8]
            if (
                QMessageBox.question(
                    self,
                    "Remover site",
                    f"Remover site '{name}'?",
                )
                != QMessageBox.StandardButton.Yes
            ):
                return
            self.archive.soft_delete_site(sid)
            self.reload()
            if self.on_changed:
                self.on_changed()

    return SitesPage


def build_programs_page() -> type:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMessageBox,
        QPushButton,
        QSpinBox,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )

    from astrocitizen.programs.models import Program
    from astrocitizen.programs.seed import seed_program_templates
    from astrocitizen.shared.ids import new_id

    class ProgramDialog(QDialog):
        def __init__(
            self,
            archive: Any,
            parent: QWidget | None = None,
            program: Program | None = None,
        ) -> None:
            super().__init__(parent)
            self.setWindowTitle("Editar programa" if program else "Novo programa")
            self._program = program
            seed_program_templates(archive)
            form = QFormLayout(self)
            self.template = QComboBox()
            for t in archive.list_program_templates():
                self.template.addItem(f"{t.id} — {t.name}", t.id)
            if program:
                idx = self.template.findData(program.template_id)
                if idx >= 0:
                    self.template.setCurrentIndex(idx)
                self.template.setEnabled(False)
            self.name = QLineEdit(program.name if program else "")
            self.state = QComboBox()
            for st in ("draft", "active", "paused", "archived"):
                self.state.addItem(st, st)
            if program:
                i = self.state.findData(program.state)
                if i >= 0:
                    self.state.setCurrentIndex(i)
            self.priority = QSpinBox()
            self.priority.setRange(1, 99)
            self.priority.setValue(program.priority if program else 10)
            form.addRow("Template PO-*", self.template)
            form.addRow("Nome", self.name)
            form.addRow("Estado", self.state)
            form.addRow("Prioridade", self.priority)
            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )
            buttons.accepted.connect(self.accept)
            buttons.rejected.connect(self.reject)
            form.addRow(buttons)

        def build(self, workspace_id: UUID, archive: Any) -> Program:
            tid = self.template.currentData()
            if not tid:
                raise ValueError("Template obrigatorio")
            tpl = archive.get_program_template(str(tid))
            name = self.name.text().strip()
            if not name:
                name = tpl.name if tpl else str(tid)
            base = self._program
            networks = list(base.export_networks) if base else list(
                tpl.default_networks if tpl else []
            )
            return Program(
                id=base.id if base else new_id(),
                workspace_id=workspace_id,
                template_id=str(tid),
                name=name,
                state=str(self.state.currentData()),  # type: ignore[arg-type]
                priority=int(self.priority.value()),
                default_instrument_config_id=(
                    base.default_instrument_config_id if base else None
                ),
                export_networks=networks,
                minimum_product=(
                    base.minimum_product
                    if base
                    else (tpl.minimum_product if tpl else "")
                ),
                cadence=dict(base.cadence) if base else {},
                settings=dict(base.settings) if base else {},
                version=base.version if base else 1,
            )

    class ProgramsPage(QWidget):
        def __init__(
            self,
            archive: Any,
            *,
            on_changed: Callable[[], None] | None = None,
        ) -> None:
            super().__init__()
            self.archive = archive
            self.on_changed = on_changed
            self._ids: list[UUID] = []
            lay = QVBoxLayout(self)
            lay.setContentsMargins(16, 12, 16, 12)
            self.title = QLabel("Programas")
            self.title.setObjectName("pageTitle")
            bar = QHBoxLayout()
            self.btn_new = QPushButton("Novo")
            self.btn_edit = QPushButton("Editar")
            self.btn_del = QPushButton("Remover")
            self.btn_refresh = QPushButton("Atualizar")
            for b in (self.btn_new, self.btn_edit, self.btn_del, self.btn_refresh):
                bar.addWidget(b)
            bar.addStretch(1)
            self.empty = QLabel()
            self.empty.setObjectName("emptyState")
            self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.empty.hide()
            self.table = QTableWidget(0, 4)
            self.table.setAlternatingRowColors(True)
            self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
            self.table.horizontalHeader().setStretchLastSection(True)
            self.table.setHorizontalHeaderLabels(["Template", "Estado", "Pri", "Nome"])
            lay.addWidget(self.title)
            lay.addLayout(bar)
            lay.addWidget(self.empty)
            lay.addWidget(self.table, 1)
            self.btn_new.clicked.connect(self._new)
            self.btn_edit.clicked.connect(self._edit)
            self.btn_del.clicked.connect(self._delete)
            self.btn_refresh.clicked.connect(self.reload)

        def _workspace(self):
            ws = self.archive.list_workspaces()
            return ws[0] if ws else None

        def reload(self) -> None:
            ws = self._workspace()
            progs = self.archive.list_programs(ws.id) if ws else []
            self._ids = [p.id for p in progs]
            self.title.setText(f"Programas ({len(progs)})")
            self.table.setRowCount(len(progs))
            for r, p in enumerate(progs):
                for c, v in enumerate(
                    [p.template_id, p.state, str(p.priority), p.name]
                ):
                    self.table.setItem(r, c, QTableWidgetItem(v))
            if progs:
                self.empty.hide()
                self.table.show()
            else:
                self.empty.setText(
                    "Nenhum programa. Use Novo (template PO-*) ou CLI."
                )
                self.empty.show()
                self.table.hide()

        def _selected_id(self) -> UUID | None:
            rows = self.table.selectionModel().selectedRows()
            if not rows:
                return None
            i = rows[0].row()
            if 0 <= i < len(self._ids):
                return self._ids[i]
            return None

        def _new(self) -> None:
            ws = self._workspace()
            if ws is None:
                QMessageBox.warning(self, "Programas", "Sem workspace.")
                return
            dlg = ProgramDialog(self.archive, self)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
            try:
                prog = dlg.build(ws.id, self.archive)
            except ValueError as e:
                QMessageBox.warning(self, "Programas", str(e))
                return
            self.archive.upsert_program(prog)
            self.reload()
            if self.on_changed:
                self.on_changed()

        def _edit(self) -> None:
            pid = self._selected_id()
            ws = self._workspace()
            if pid is None or ws is None:
                QMessageBox.information(self, "Programas", "Selecione um programa.")
                return
            prog = self.archive.get_program(pid)
            if prog is None:
                return
            dlg = ProgramDialog(self.archive, self, prog)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
            try:
                updated = dlg.build(ws.id, self.archive)
            except ValueError as e:
                QMessageBox.warning(self, "Programas", str(e))
                return
            self.archive.upsert_program(updated)
            self.reload()
            if self.on_changed:
                self.on_changed()

        def _delete(self) -> None:
            pid = self._selected_id()
            if pid is None:
                QMessageBox.information(self, "Programas", "Selecione um programa.")
                return
            prog = self.archive.get_program(pid)
            name = prog.name if prog else str(pid)[:8]
            if (
                QMessageBox.question(
                    self,
                    "Remover programa",
                    f"Remover programa '{name}'?",
                )
                != QMessageBox.StandardButton.Yes
            ):
                return
            self.archive.soft_delete_program(pid)
            self.reload()
            if self.on_changed:
                self.on_changed()

    return ProgramsPage


def build_targets_page() -> type:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QDoubleSpinBox,
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

    from astrocitizen.planning.models import Target
    from astrocitizen.shared.ids import new_id

    class TargetDialog(QDialog):
        def __init__(
            self,
            archive: Any,
            workspace_id: UUID,
            parent: QWidget | None = None,
            target: Target | None = None,
        ) -> None:
            super().__init__(parent)
            self.setWindowTitle("Editar alvo" if target else "Novo alvo")
            self._target = target
            self._workspace_id = workspace_id
            form = QFormLayout(self)
            self.designation = QLineEdit(target.designation if target else "")
            self.ra = QDoubleSpinBox()
            self.ra.setRange(0, 360)
            self.ra.setDecimals(6)
            self.ra.setSpecialValueText("-")
            self.ra.setValue(target.ra_deg if target and target.ra_deg is not None else 0.0)
            self.dec = QDoubleSpinBox()
            self.dec.setRange(-90, 90)
            self.dec.setDecimals(6)
            self.dec.setValue(target.dec_deg if target and target.dec_deg is not None else 0.0)
            self.ttype = QLineEdit(target.target_type if target else "star")
            self.link_prog = QComboBox()
            self.link_prog.addItem("(sem ligacao)", None)
            for p in archive.list_programs(workspace_id):
                self.link_prog.addItem(f"{p.template_id} · {p.name}", p.id)
            form.addRow("Designacao", self.designation)
            form.addRow("RA (deg)", self.ra)
            form.addRow("Dec (deg)", self.dec)
            form.addRow("Tipo", self.ttype)
            form.addRow("Ligar a programa", self.link_prog)
            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )
            buttons.accepted.connect(self.accept)
            buttons.rejected.connect(self.reject)
            form.addRow(buttons)

        def build(self) -> tuple[Target, UUID | None]:
            name = self.designation.text().strip()
            if not name:
                raise ValueError("Designacao obrigatoria")
            base = self._target
            target = Target(
                id=base.id if base else new_id(),
                workspace_id=self._workspace_id,
                designation=name,
                ra_deg=float(self.ra.value()),
                dec_deg=float(self.dec.value()),
                target_type=self.ttype.text().strip() or "star",
                external_ids=dict(base.external_ids) if base else {},
                version=base.version if base else 1,
            )
            return target, self.link_prog.currentData()

    class TargetsPage(QWidget):
        def __init__(
            self,
            archive: Any,
            *,
            on_changed: Callable[[], None] | None = None,
        ) -> None:
            super().__init__()
            self.archive = archive
            self.on_changed = on_changed
            self._ids: list[UUID] = []
            lay = QVBoxLayout(self)
            lay.setContentsMargins(16, 12, 16, 12)
            self.title = QLabel("Alvos")
            self.title.setObjectName("pageTitle")
            bar = QHBoxLayout()
            self.btn_new = QPushButton("Novo")
            self.btn_edit = QPushButton("Editar")
            self.btn_del = QPushButton("Remover")
            self.btn_refresh = QPushButton("Atualizar")
            for b in (self.btn_new, self.btn_edit, self.btn_del, self.btn_refresh):
                bar.addWidget(b)
            bar.addStretch(1)
            self.empty = QLabel()
            self.empty.setObjectName("emptyState")
            self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.empty.hide()
            self.table = QTableWidget(0, 4)
            self.table.setAlternatingRowColors(True)
            self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
            self.table.horizontalHeader().setStretchLastSection(True)
            self.table.setHorizontalHeaderLabels(["Designacao", "RA", "Dec", "Tipo"])
            lay.addWidget(self.title)
            lay.addLayout(bar)
            lay.addWidget(self.empty)
            lay.addWidget(self.table, 1)
            self.btn_new.clicked.connect(self._new)
            self.btn_edit.clicked.connect(self._edit)
            self.btn_del.clicked.connect(self._delete)
            self.btn_refresh.clicked.connect(self.reload)

        def _workspace(self):
            ws = self.archive.list_workspaces()
            return ws[0] if ws else None

        def reload(self) -> None:
            ws = self._workspace()
            targets = self.archive.list_targets(ws.id) if ws else []
            self._ids = [t.id for t in targets]
            self.title.setText(f"Alvos ({len(targets)})")
            self.table.setRowCount(len(targets))
            for r, t in enumerate(targets):
                vals = [
                    t.designation,
                    f"{t.ra_deg:.4f}" if t.ra_deg is not None else "-",
                    f"{t.dec_deg:.4f}" if t.dec_deg is not None else "-",
                    t.target_type,
                ]
                for c, v in enumerate(vals):
                    self.table.setItem(r, c, QTableWidgetItem(v))
            if targets:
                self.empty.hide()
                self.table.show()
            else:
                self.empty.setText("Nenhum alvo. Use Novo ou CLI: astrocitizen target add")
                self.empty.show()
                self.table.hide()

        def _selected_id(self) -> UUID | None:
            rows = self.table.selectionModel().selectedRows()
            if not rows:
                return None
            i = rows[0].row()
            if 0 <= i < len(self._ids):
                return self._ids[i]
            return None

        def _new(self) -> None:
            ws = self._workspace()
            if ws is None:
                QMessageBox.warning(self, "Alvos", "Sem workspace.")
                return
            dlg = TargetDialog(self.archive, ws.id, self)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
            try:
                target, prog_id = dlg.build()
            except ValueError as e:
                QMessageBox.warning(self, "Alvos", str(e))
                return
            self.archive.upsert_target(target)
            if prog_id is not None:
                self.archive.link_program_target(prog_id, target.id)
            self.reload()
            if self.on_changed:
                self.on_changed()

        def _edit(self) -> None:
            tid = self._selected_id()
            ws = self._workspace()
            if tid is None or ws is None:
                QMessageBox.information(self, "Alvos", "Selecione um alvo.")
                return
            target = self.archive.get_target(tid)
            if target is None:
                return
            dlg = TargetDialog(self.archive, ws.id, self, target)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
            try:
                updated, prog_id = dlg.build()
            except ValueError as e:
                QMessageBox.warning(self, "Alvos", str(e))
                return
            self.archive.upsert_target(updated)
            if prog_id is not None:
                self.archive.link_program_target(prog_id, updated.id)
            self.reload()
            if self.on_changed:
                self.on_changed()

        def _delete(self) -> None:
            tid = self._selected_id()
            if tid is None:
                QMessageBox.information(self, "Alvos", "Selecione um alvo.")
                return
            target = self.archive.get_target(tid)
            name = target.designation if target else str(tid)[:8]
            if (
                QMessageBox.question(
                    self,
                    "Remover alvo",
                    f"Remover alvo '{name}'?",
                )
                != QMessageBox.StandardButton.Yes
            ):
                return
            self.archive.soft_delete_target(tid)
            self.reload()
            if self.on_changed:
                self.on_changed()

    return TargetsPage
