"""Painel Ajuda in-app (RN-121)."""

from __future__ import annotations

from typing import Any


def build_help_panel() -> type:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    from astrocitizen.shared.i18n import (
        help_topic_body,
        help_topic_ids,
        help_topic_title,
        t,
    )

    class HelpPanel(QWidget):
        def __init__(self, parent: QWidget | None = None) -> None:
            super().__init__(parent)
            root = QVBoxLayout(self)
            root.setContentsMargins(16, 12, 16, 12)
            self.title = QLabel()
            self.title.setObjectName("pageTitle")
            root.addWidget(self.title)

            row = QHBoxLayout()
            left = QVBoxLayout()
            self.topics_label = QLabel()
            self.topics_label.setObjectName("emptyState")
            left.addWidget(self.topics_label)
            self.list = QListWidget()
            self.list.currentRowChanged.connect(self._on_row)
            left.addWidget(self.list, 1)
            row.addLayout(left, 1)

            self.body = QTextEdit()
            self.body.setReadOnly(True)
            row.addWidget(self.body, 2)
            root.addLayout(row, 1)
            self.retranslate()

        def retranslate(self) -> None:
            self.title.setText(t("help.panel_title"))
            self.topics_label.setText(t("help.topics"))
            current = self.list.currentRow()
            self.list.clear()
            for tid in help_topic_ids():
                item = QListWidgetItem(help_topic_title(tid))
                item.setData(Qt.ItemDataRole.UserRole, tid)
                self.list.addItem(item)
            if self.list.count():
                idx = current if 0 <= current < self.list.count() else 0
                self.list.setCurrentRow(idx)
                self._on_row(idx)

        def select_topic(self, topic_id: str) -> None:
            for i in range(self.list.count()):
                item = self.list.item(i)
                if item and item.data(Qt.ItemDataRole.UserRole) == topic_id:
                    self.list.setCurrentRow(i)
                    return
            if self.list.count():
                self.list.setCurrentRow(0)

        def _on_row(self, row: int) -> None:
            if row < 0:
                return
            item = self.list.item(row)
            if item is None:
                return
            tid = str(item.data(Qt.ItemDataRole.UserRole) or "")
            self.body.setPlainText(help_topic_body(tid))

    return HelpPanel


def area_to_help_topic(area_name: str) -> str:
    """Map nav area key to help topic id."""
    mapping = {
        "Noite": "night",
        "Observatorio": "observatory",
        "Analisar": "analyze",
        "Contribuir": "contribute",
        "Arquivo": "archive",
        "Configurar": "configure",
    }
    return mapping.get(area_name, "getting_started")
