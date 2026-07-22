"""Preferencias desktop: idioma UI (RN-120)."""

from __future__ import annotations

from typing import Any, Callable


def build_prefs_panel() -> type:
    from PySide6.QtWidgets import (
        QComboBox,
        QFormLayout,
        QLabel,
        QVBoxLayout,
        QWidget,
    )

    from astrocitizen.desktop.theme import load_ui_lang_pref, save_ui_lang_pref
    from astrocitizen.shared.i18n import (
        detect_system_lang,
        get_current_lang,
        resolve_ui_lang,
        set_current_lang,
        t,
    )

    class PrefsPanel(QWidget):
        def __init__(
            self,
            *,
            on_language_changed: Callable[[str], None] | None = None,
            parent: QWidget | None = None,
        ) -> None:
            super().__init__(parent)
            self.on_language_changed = on_language_changed
            root = QVBoxLayout(self)
            root.setContentsMargins(16, 12, 16, 12)
            self.title = QLabel()
            self.title.setObjectName("pageTitle")
            root.addWidget(self.title)

            form = QFormLayout()
            self.lang_label = QLabel()
            self.lang_combo = QComboBox()
            form.addRow(self.lang_label, self.lang_combo)
            root.addLayout(form)

            self.hint = QLabel()
            self.hint.setObjectName("emptyState")
            self.hint.setWordWrap(True)
            root.addWidget(self.hint)
            self.effective = QLabel()
            self.effective.setObjectName("emptyState")
            root.addWidget(self.effective)
            root.addStretch(1)

            self._filling = False
            self.lang_combo.currentIndexChanged.connect(self._on_combo)
            self.retranslate()
            self._reload_combo()

        def _reload_combo(self) -> None:
            self._filling = True
            self.lang_combo.clear()
            options = (
                ("auto", "prefs.lang.auto"),
                ("pt", "prefs.lang.pt"),
                ("es", "prefs.lang.es"),
                ("en", "prefs.lang.en"),
            )
            for code, key in options:
                self.lang_combo.addItem(t(key), code)
            pref = load_ui_lang_pref()
            i = self.lang_combo.findData(pref)
            self.lang_combo.setCurrentIndex(i if i >= 0 else 0)
            self._filling = False
            self._update_effective()

        def retranslate(self) -> None:
            self.title.setText(t("prefs.title"))
            self.lang_label.setText(t("prefs.language"))
            self.hint.setText(t("prefs.hint"))
            # refresh combo labels without losing selection
            pref = self.lang_combo.currentData() or load_ui_lang_pref()
            self._filling = True
            for i in range(self.lang_combo.count()):
                code = self.lang_combo.itemData(i)
                key = {
                    "auto": "prefs.lang.auto",
                    "pt": "prefs.lang.pt",
                    "es": "prefs.lang.es",
                    "en": "prefs.lang.en",
                }.get(str(code), "prefs.lang.auto")
                self.lang_combo.setItemText(i, t(key))
            j = self.lang_combo.findData(pref)
            if j >= 0:
                self.lang_combo.setCurrentIndex(j)
            self._filling = False
            self._update_effective()

        def _update_effective(self) -> None:
            self.effective.setText(
                t("prefs.effective", ui_lang=get_current_lang())
            )

        def _on_combo(self, *_args: Any) -> None:
            if self._filling:
                return
            pref = str(self.lang_combo.currentData() or "auto")
            save_ui_lang_pref(pref)
            lang = resolve_ui_lang(pref, detected=detect_system_lang())
            set_current_lang(lang)
            self._update_effective()
            if self.on_language_changed:
                self.on_language_changed(lang)

    return PrefsPanel
