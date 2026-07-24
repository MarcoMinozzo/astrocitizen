"""Painel Campanhas AAVSO — browser embutido (Qt WebEngine) ou fallback (AC-095)."""

from __future__ import annotations

import os
from typing import Any


def webengine_available() -> bool:
    """WebEngine embutido é opt-in: ASTROCITIZEN_WEBENGINE=1.

    Em várias GPUs/Linux o Chromium do QtWebEngine segfaulta ao carregar o
    portal AAVSO no arranque; o fallback (browser do SO) é o default estável.
    """
    flag = (os.environ.get("ASTROCITIZEN_WEBENGINE") or "").strip().lower()
    if flag not in ("1", "true", "yes", "on"):
        return False
    if (os.environ.get("ASTROCITIZEN_NO_WEBENGINE") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    ):
        return False
    try:
        from PySide6.QtWebEngineWidgets import QWebEngineView  # noqa: F401

        return True
    except ImportError:
        return False


def build_aavso_campaigns_browser() -> type:
    from PySide6.QtCore import QUrl, Qt
    from PySide6.QtGui import QDesktopServices
    from PySide6.QtWidgets import (
        QHBoxLayout,
        QLabel,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

    from astrocitizen.adapters.aavso_portal import (
        AAVSO_CAMPAIGNS_HOME,
        campaign_status_label,
        is_aavso_host,
    )

    class AavsoCampaignsBrowser(QWidget):
        def __init__(self, parent: QWidget | None = None) -> None:
            super().__init__(parent)
            self._view: Any = None
            root = QVBoxLayout(self)
            root.setContentsMargins(12, 8, 12, 8)
            root.setSpacing(8)

            title = QLabel("Campanhas AAVSO")
            title.setObjectName("pageTitle")
            root.addWidget(title)

            hint = QLabel(
                "Portal Observing Campaigns (sem API publica). "
                "Por defeito abre no browser do sistema (mais estavel). "
                "Browser embutido: ASTROCITIZEN_WEBENGINE=1 e "
                "pip install 'astrocitizen[gui-web]'."
            )
            hint.setObjectName("emptyState")
            hint.setWordWrap(True)
            root.addWidget(hint)

            bar = QHBoxLayout()
            self.btn_back = QPushButton("←")
            self.btn_back.setObjectName("secondaryBtn")
            self.btn_back.setFixedWidth(36)
            self.btn_back.setToolTip("Voltar")
            self.btn_fwd = QPushButton("→")
            self.btn_fwd.setObjectName("secondaryBtn")
            self.btn_fwd.setFixedWidth(36)
            self.btn_fwd.setToolTip("Avancar")
            self.btn_reload = QPushButton("Recarregar")
            self.btn_reload.setObjectName("secondaryBtn")
            self.btn_home = QPushButton("Inicio")
            self.btn_home.setObjectName("secondaryBtn")
            self.btn_external = QPushButton("Abrir no browser")
            self.btn_external.setObjectName("secondaryBtn")
            for w in (
                self.btn_back,
                self.btn_fwd,
                self.btn_reload,
                self.btn_home,
                self.btn_external,
            ):
                bar.addWidget(w)
            bar.addStretch(1)
            root.addLayout(bar)

            self.status = QLabel("")
            self.status.setObjectName("emptyState")
            self.status.setWordWrap(True)
            root.addWidget(self.status)

            self._home = AAVSO_CAMPAIGNS_HOME
            self._current_url = self._home

            if webengine_available():
                self._build_webengine(root)
            else:
                self._build_fallback(root)

            self.btn_home.clicked.connect(self._go_home)
            self.btn_external.clicked.connect(self._open_external)
            self.btn_reload.clicked.connect(self._reload)
            self.btn_back.clicked.connect(self._go_back)
            self.btn_fwd.clicked.connect(self._go_forward)
            self._sync_nav_buttons()
            self._update_status(self._current_url)

        def _build_webengine(self, root: QVBoxLayout) -> None:
            from PySide6.QtWebEngineCore import QWebEnginePage
            from PySide6.QtWebEngineWidgets import QWebEngineView

            class _GuardedPage(QWebEnginePage):
                def __init__(self, outer: "AavsoCampaignsBrowser", parent: Any = None):
                    super().__init__(parent)
                    self._outer = outer

                def acceptNavigationRequest(  # noqa: N802
                    self, url: QUrl, _type: Any, is_main_frame: bool
                ) -> bool:
                    if not is_main_frame:
                        return True
                    s = url.toString()
                    if is_aavso_host(s):
                        return True
                    QDesktopServices.openUrl(url)
                    return False

            view = QWebEngineView(self)
            page = _GuardedPage(self, view)
            view.setPage(page)
            view.load(QUrl(self._home))
            view.urlChanged.connect(self._on_url_changed)
            view.loadFinished.connect(lambda _ok: self._sync_nav_buttons())
            root.addWidget(view, 1)
            self._view = view

        def _build_fallback(self, root: QVBoxLayout) -> None:
            self.btn_back.setEnabled(False)
            self.btn_fwd.setEnabled(False)
            self.btn_reload.setEnabled(False)
            msg = QLabel(
                "Portal no browser do sistema (recomendado).\n\n"
                "Use «Abrir no browser» para Observing Campaigns.\n"
                "Embutido (instavel em alguns PCs): "
                "ASTROCITIZEN_WEBENGINE=1 e pip install 'astrocitizen[gui-web]'."
            )
            msg.setObjectName("emptyState")
            msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            msg.setWordWrap(True)
            root.addWidget(msg, 1)
            self.status.setText(f"Fallback · {self._home}")

        def _on_url_changed(self, url: QUrl) -> None:
            self._current_url = url.toString()
            self._update_status(self._current_url)
            self._sync_nav_buttons()

        def _update_status(self, url: str) -> None:
            label = campaign_status_label(url)
            if label:
                self.status.setText(f"{label} · {url}")
            else:
                self.status.setText(url)

        def _sync_nav_buttons(self) -> None:
            if self._view is None:
                return
            hist = self._view.history()
            self.btn_back.setEnabled(hist.canGoBack())
            self.btn_fwd.setEnabled(hist.canGoForward())

        def _go_home(self) -> None:
            self._current_url = self._home
            if self._view is not None:
                self._view.load(QUrl(self._home))
            else:
                self._update_status(self._home)
                self._open_external()

        def _reload(self) -> None:
            if self._view is not None:
                self._view.reload()

        def _go_back(self) -> None:
            if self._view is not None:
                self._view.back()

        def _go_forward(self) -> None:
            if self._view is not None:
                self._view.forward()

        def _open_external(self) -> None:
            QDesktopServices.openUrl(QUrl(self._current_url or self._home))

        def reload(self) -> None:
            """Compat shell refresh — nao recarrega a pagina web."""
            return

    return AavsoCampaignsBrowser
