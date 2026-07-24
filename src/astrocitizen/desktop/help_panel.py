"""Painel Ajuda in-app (RN-121) + pergunta grounded KB (AC-196)."""

from __future__ import annotations

from typing import Any


def build_help_panel() -> type:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QPushButton,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    from astrocitizen.adapters.sqlite.hybrid_retriever import HybridRetriever
    from astrocitizen.knowledge.assistant import answer_help
    from astrocitizen.shared.i18n import (
        help_topic_body,
        help_topic_ids,
        help_topic_title,
        t,
    )

    class HelpPanel(QWidget):
        def __init__(
            self,
            parent: QWidget | None = None,
            *,
            archive: Any | None = None,
        ) -> None:
            super().__init__(parent)
            self._archive = archive
            root = QVBoxLayout(self)
            root.setContentsMargins(16, 12, 16, 12)
            self.title = QLabel()
            self.title.setObjectName("pageTitle")
            root.addWidget(self.title)

            ask_row = QHBoxLayout()
            self.ask_input = QLineEdit()
            self.ask_input.returnPressed.connect(self._ask_kb)
            ask_row.addWidget(self.ask_input, 1)
            self.ask_btn = QPushButton()
            self.ask_btn.clicked.connect(self._ask_kb)
            ask_row.addWidget(self.ask_btn)
            root.addLayout(ask_row)
            self.ask_hint = QLabel()
            self.ask_hint.setObjectName("emptyState")
            self.ask_hint.setWordWrap(True)
            root.addWidget(self.ask_hint)

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

        def set_archive(self, archive: Any | None) -> None:
            self._archive = archive

        def retranslate(self) -> None:
            self.title.setText(t("help.panel_title"))
            self.topics_label.setText(t("help.topics"))
            self.ask_input.setPlaceholderText(t("help.ask_placeholder"))
            self.ask_btn.setText(t("help.ask_button"))
            self.ask_hint.setText(t("help.ask_hint"))
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

        def _ask_kb(self) -> None:
            q = self.ask_input.text().strip()
            if not q:
                self.body.setPlainText(t("help.ask_empty"))
                return
            if self._archive is None:
                self.body.setPlainText(t("help.ask_no_archive"))
                return
            try:
                retriever = HybridRetriever(self._archive)
                ans = answer_help(retriever, q, limit=5, mode="hybrid")
                self.body.setPlainText(ans.format_text())
            except Exception as exc:  # noqa: BLE001 — UI boundary
                self.body.setPlainText(f"{t('help.ask_error')}\n{exc}")

    return HelpPanel


def area_to_help_topic(area_name: str) -> str:
    """Map nav area key to help topic id."""
    mapping = {
        "Noite": "night",
        "Observatorio": "observatory",
        "Catalogo": "catalog",
        "Analisar": "analyze",
        "Contribuir": "contribute",
        "Arquivo": "archive",
        "Configurar": "configure",
    }
    return mapping.get(area_name, "getting_started")
