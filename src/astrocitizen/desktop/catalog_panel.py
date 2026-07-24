"""Painel Catálogo — ficha celeste por secções (AC-235)."""

from __future__ import annotations

from typing import Any
from uuid import UUID


def build_catalog_dashboard() -> type:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QCheckBox,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMessageBox,
        QPushButton,
        QScrollArea,
        QSplitter,
        QVBoxLayout,
        QWidget,
    )

    from astrocitizen.catalog.dossier import CatalogDossierService
    from astrocitizen.catalog.models import (
        SECTION_FIELDS,
        SECTION_LABELS,
        SECTION_ORDER,
    )
    from astrocitizen.shared.errors import DomainError, NotFoundError

    class CatalogDashboard(QWidget):
        def __init__(self, archive: Any) -> None:
            super().__init__()
            self.archive = archive
            self._svc = CatalogDossierService(archive)
            self._ids: list[UUID] = []
            self._fields: dict[str, dict[str, QLineEdit]] = {}

            root = QVBoxLayout(self)
            root.setContentsMargins(16, 12, 16, 12)
            self.title = QLabel("Catalogo")
            self.title.setObjectName("pageTitle")
            root.addWidget(self.title)

            hint = QLabel(
                "Pesquise um objecto: consultamos Sesame, VSX, SIMBAD, VizieR e Gaia "
                "e gravamos a ficha no nosso catalogo (buffer local + sync)."
            )
            hint.setWordWrap(True)
            hint.setObjectName("hintText")
            root.addWidget(hint)

            search_row = QHBoxLayout()
            self.search = QLineEdit()
            self.search.setPlaceholderText('ex.: "SS Cyg", "M31", "HD 209458"')
            self.search.returnPressed.connect(self._lookup)
            self.cache_only = QCheckBox("So cache (sem rede)")
            self.btn_lookup = QPushButton("Buscar / actualizar")
            self.btn_lookup.setObjectName("primaryBtn")
            self.btn_lookup.clicked.connect(self._lookup)
            self.btn_refresh = QPushButton("Actualizar lista")
            self.btn_refresh.clicked.connect(self.reload)
            search_row.addWidget(self.search, 1)
            search_row.addWidget(self.cache_only)
            search_row.addWidget(self.btn_lookup)
            search_row.addWidget(self.btn_refresh)
            root.addLayout(search_row)

            self.status = QLabel("")
            self.status.setObjectName("hintText")
            root.addWidget(self.status)

            split = QSplitter(Qt.Orientation.Horizontal)
            left = QWidget()
            left_l = QVBoxLayout(left)
            left_l.setContentsMargins(0, 0, 0, 0)
            left_l.addWidget(QLabel("Fichas no catalogo"))
            self.list = QListWidget()
            self.list.currentRowChanged.connect(self._on_select)
            left_l.addWidget(self.list, 1)
            split.addWidget(left)

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            form_host = QWidget()
            form_l = QVBoxLayout(form_host)
            form_l.setContentsMargins(8, 0, 0, 0)
            for section in SECTION_ORDER:
                box = QGroupBox(SECTION_LABELS.get(section, section))
                form = QFormLayout(box)
                self._fields[section] = {}
                for key, label in SECTION_FIELDS[section]:
                    edit = QLineEdit()
                    edit.setReadOnly(True)
                    self._fields[section][key] = edit
                    form.addRow(label, edit)
                form_l.addWidget(box)
            form_l.addStretch(1)
            scroll.setWidget(form_host)
            split.addWidget(scroll)
            split.setStretchFactor(0, 1)
            split.setStretchFactor(1, 3)
            root.addWidget(split, 1)

        def _workspace(self):
            ws = self.archive.list_workspaces()
            return ws[0] if ws else None

        def reload(self) -> None:
            ws = self._workspace()
            objects = self._svc.list(ws.id, limit=200) if ws else []
            self._ids = [o.id for o in objects]
            self.list.clear()
            for o in objects:
                src = ", ".join(o.sources[:4]) if o.sources else "-"
                item = QListWidgetItem(f"{o.designation}  ·  {src}")
                item.setToolTip(o.query_name)
                self.list.addItem(item)
            self.title.setText(f"Catalogo ({len(objects)})")

        def _clear_form(self) -> None:
            for section_fields in self._fields.values():
                for edit in section_fields.values():
                    edit.clear()

        def _fill_form(self, obj: Any) -> None:
            for section, fields in self._fields.items():
                for key, edit in fields.items():
                    val = obj.field_value(section, key)
                    if val is None:
                        edit.setText("")
                    elif isinstance(val, (dict, list)):
                        edit.setText(str(val))
                    else:
                        edit.setText(str(val))

        def _on_select(self, row: int) -> None:
            if row < 0 or row >= len(self._ids):
                self._clear_form()
                return
            obj = self._svc.get(self._ids[row])
            if obj is None:
                self._clear_form()
                return
            self.search.setText(obj.query_name or obj.designation)
            self._fill_form(obj)

        def _lookup(self) -> None:
            ws = self._workspace()
            if ws is None:
                QMessageBox.warning(self, "Catalogo", "Sem workspace.")
                return
            name = self.search.text().strip()
            if not name:
                QMessageBox.information(
                    self, "Catalogo", "Indique o nome do objecto celeste."
                )
                return
            self.btn_lookup.setEnabled(False)
            self.status.setText("A consultar APIs…")
            try:
                obj = self._svc.lookup(
                    ws.id,
                    name,
                    network=not self.cache_only.isChecked(),
                )
            except (NotFoundError, DomainError) as exc:
                self.status.setText("")
                QMessageBox.warning(self, "Catalogo", str(exc))
                return
            except Exception as exc:  # noqa: BLE001 — UI boundary
                self.status.setText("")
                QMessageBox.critical(self, "Catalogo", str(exc))
                return
            finally:
                self.btn_lookup.setEnabled(True)

            src = ", ".join(obj.sources) if obj.sources else "(sem fontes)"
            self.status.setText(
                f"Gravado: {obj.designation}  ·  fontes: {src}  ·  v{obj.version}"
            )
            self.reload()
            try:
                idx = self._ids.index(obj.id)
            except ValueError:
                idx = 0
            self.list.setCurrentRow(idx)
            self._fill_form(obj)

    return CatalogDashboard
