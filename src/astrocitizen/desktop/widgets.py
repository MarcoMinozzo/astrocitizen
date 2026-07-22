"""Widgets partilhados do shell desktop (U0)."""

from __future__ import annotations

from typing import Any
from uuid import UUID


def refill_site_combo(
    combo: Any,
    sites: list[Any],
    *,
    current: UUID | None = None,
    none_label: str = "(nenhum)",
    with_none: bool = True,
) -> None:
    """Repoe itens de um QComboBox de sites; preserva `current` se possivel."""
    combo.clear()
    if with_none:
        combo.addItem(none_label, None)
    for s in sites:
        combo.addItem(s.name, s.id)
    if current is not None:
        i = combo.findData(current)
        if i >= 0:
            combo.setCurrentIndex(i)


def refill_program_combo(
    combo: Any,
    programs: list[Any],
    *,
    current: UUID | None = None,
    none_label: str = "(nenhum)",
    sep: str = " · ",
) -> None:
    """Repoe programas como `template · name`."""
    combo.clear()
    combo.addItem(none_label, None)
    for p in programs:
        combo.addItem(f"{p.template_id}{sep}{p.name}", p.id)
    if current is not None:
        i = combo.findData(current)
        if i >= 0:
            combo.setCurrentIndex(i)


def select_combo_data(combo: Any, data: object) -> bool:
    """Selecciona item por userData; True se encontrado."""
    if combo is None:
        return False
    i = combo.findData(data)
    if i < 0:
        return False
    combo.blockSignals(True)
    combo.setCurrentIndex(i)
    combo.blockSignals(False)
    return True


def build_shared_widgets() -> dict[str, type]:
    """Factories Qt: PathBrowseRow, ContextBar, TabHub (requer PySide6)."""
    from PySide6.QtCore import Signal
    from PySide6.QtWidgets import (
        QComboBox,
        QDateEdit,
        QFrame,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )

    from astrocitizen.desktop.theme import viability_badge

    class PathBrowseRow(QWidget):
        """LineEdit + botao secondary para ficheiro/pasta."""

        def __init__(
            self,
            *,
            button_label: str = "...",
            placeholder: str = "",
            parent: QWidget | None = None,
        ) -> None:
            super().__init__(parent)
            self.edit = QLineEdit()
            if placeholder:
                self.edit.setPlaceholderText(placeholder)
            self.button = QPushButton(button_label)
            self.button.setObjectName("secondaryBtn")
            row = QHBoxLayout(self)
            row.setContentsMargins(0, 0, 0, 0)
            row.addWidget(self.edit, 1)
            row.addWidget(self.button)

        def path_text(self) -> str:
            return self.edit.text().strip()

        def set_path(self, path: str) -> None:
            self.edit.setText(path)

    class ContextBar(QFrame):
        """Barra global: site, programa, data da noite, badge."""

        site_changed = Signal(object)
        program_changed = Signal(object)
        night_date_changed = Signal(str)

        def __init__(self, parent: QWidget | None = None) -> None:
            super().__init__(parent)
            self.setObjectName("contextBar")
            lay = QHBoxLayout(self)
            lay.setContentsMargins(16, 6, 16, 6)
            lay.setSpacing(10)

            self._lbl_site = QLabel("Site")
            lay.addWidget(self._lbl_site)
            self.site = QComboBox()
            self.site.setMinimumWidth(140)
            lay.addWidget(self.site)

            self._lbl_program = QLabel("Programa")
            lay.addWidget(self._lbl_program)
            self.program = QComboBox()
            self.program.setMinimumWidth(160)
            lay.addWidget(self.program)

            self._lbl_night = QLabel("Noite")
            lay.addWidget(self._lbl_night)
            self.night_date = QDateEdit()
            self.night_date.setCalendarPopup(True)
            self.night_date.setDisplayFormat("yyyy-MM-dd")
            from PySide6.QtCore import QDate

            self.night_date.setDate(QDate.currentDate())
            lay.addWidget(self.night_date)

            self.badge = QLabel("-")
            self.badge.setObjectName("badgeIdle")
            lay.addWidget(self.badge)
            lay.addStretch(1)

            self.site.currentIndexChanged.connect(self._emit_site)
            self.program.currentIndexChanged.connect(self._emit_program)
            self.night_date.dateChanged.connect(self._emit_date)

        def retranslate(self) -> None:
            from astrocitizen.shared.i18n import t

            self._lbl_site.setText(t("context.site"))
            self._lbl_program.setText(t("context.program"))
            self._lbl_night.setText(t("context.night"))

        def _emit_site(self, *_args: object) -> None:
            self.site_changed.emit(self.site.currentData())

        def _emit_program(self, *_args: object) -> None:
            self.program_changed.emit(self.program.currentData())

        def _emit_date(self, *_args: object) -> None:
            self.night_date_changed.emit(self.night_date.date().toString("yyyy-MM-dd"))

        def reload(
            self,
            *,
            sites: list[Any],
            programs: list[Any],
            site_id: UUID | None = None,
            program_id: UUID | None = None,
            viable: bool | None = None,
        ) -> None:
            cur_s = site_id if site_id is not None else self.site.currentData()
            cur_p = program_id if program_id is not None else self.program.currentData()
            self.site.blockSignals(True)
            self.program.blockSignals(True)
            refill_site_combo(self.site, sites, current=cur_s, with_none=True)
            refill_program_combo(self.program, programs, current=cur_p)
            self.site.blockSignals(False)
            self.program.blockSignals(False)
            self.set_viability(viable)

        def set_viability(self, ok: bool | None) -> None:
            label, obj = viability_badge(ok)
            self.badge.setText(label)
            self.badge.setObjectName(obj)
            self.badge.style().unpolish(self.badge)
            self.badge.style().polish(self.badge)

        def night_date_iso(self) -> str:
            return self.night_date.date().toString("yyyy-MM-dd")

    class TabHub(QWidget):
        """Pagina com titulo opcional + QTabWidget de paineis existentes."""

        def __init__(
            self,
            *,
            title: str,
            hint: str = "",
            tabs: list[tuple[str, QWidget]] | None = None,
            parent: QWidget | None = None,
        ) -> None:
            super().__init__(parent)
            root = QVBoxLayout(self)
            root.setContentsMargins(0, 0, 0, 0)
            root.setSpacing(0)
            if title:
                head = QWidget()
                hl = QVBoxLayout(head)
                hl.setContentsMargins(16, 12, 16, 4)
                t = QLabel(title)
                t.setObjectName("pageTitle")
                hl.addWidget(t)
                if hint:
                    h = QLabel(hint)
                    h.setObjectName("emptyState")
                    h.setWordWrap(True)
                    # tighter than full emptyState padding for hub hints
                    h.setStyleSheet("padding: 0 0 8px 0;")
                    hl.addWidget(h)
                root.addWidget(head)
            self.tabs = QTabWidget()
            for name, page in tabs or []:
                self.tabs.addTab(page, name)
            root.addWidget(self.tabs, 1)

        def add_tab(self, name: str, page: QWidget) -> int:
            return self.tabs.addTab(page, name)

    return {
        "PathBrowseRow": PathBrowseRow,
        "ContextBar": ContextBar,
        "TabHub": TabHub,
    }
