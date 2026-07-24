"""Viewer de mapa radar (Leaflet+RainViewer) embutido e em modal."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from astrocitizen.desktop.aavso_campaigns_browser import webengine_available
from astrocitizen.desktop.radar_map_html import write_radar_map_html


def build_radar_map_viewer() -> type:
    """Factory lazy (PySide6 opcional)."""
    from PySide6.QtCore import QUrl, Qt
    from PySide6.QtGui import QDesktopServices, QPixmap
    from PySide6.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QStackedWidget,
        QVBoxLayout,
        QWidget,
    )

    class RadarMapViewer(QWidget):
        """Mapa interactivo (WebEngine opt-in) ou PNG + abrir no browser."""

        def __init__(self, parent: QWidget | None = None) -> None:
            super().__init__(parent)
            self._lat: float | None = None
            self._lon: float | None = None
            self._site_name = ""
            self._zoom = 6
            self._html_path: Path | None = None
            self._view: Any = None

            root = QVBoxLayout(self)
            root.setContentsMargins(0, 0, 0, 0)
            root.setSpacing(4)

            head = QHBoxLayout()
            self.title = QLabel("Radar / mapa (RainViewer)")
            head.addWidget(self.title, 1)
            self.btn_modal = QPushButton("Ampliar")
            self.btn_modal.setObjectName("secondaryBtn")
            self.btn_modal.setToolTip("Abrir mapa em janela modal")
            self.btn_modal.clicked.connect(self.open_modal)
            head.addWidget(self.btn_modal)
            self.btn_browser = QPushButton("Browser")
            self.btn_browser.setObjectName("secondaryBtn")
            self.btn_browser.setToolTip("Abrir mapa interactivo no browser do sistema")
            self.btn_browser.clicked.connect(self.open_in_browser)
            head.addWidget(self.btn_browser)
            root.addLayout(head)

            self.stack = QStackedWidget()
            self.radar_label = QLabel("Radar: clique Atualizar noite")
            self.radar_label.setObjectName("radarPane")
            self.radar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.radar_label.setMinimumSize(160, 100)
            self.stack.addWidget(self.radar_label)  # index 0 = PNG / fallback

            self._web_page = QWidget()
            web_l = QVBoxLayout(self._web_page)
            web_l.setContentsMargins(0, 0, 0, 0)
            if webengine_available():
                from PySide6.QtWebEngineWidgets import QWebEngineView

                self._view = QWebEngineView(self._web_page)
                web_l.addWidget(self._view, 1)
                self.stack.addWidget(self._web_page)  # index 1
            else:
                hint = QLabel(
                    "Mapa interactivo embutido: ASTROCITIZEN_WEBENGINE=1 "
                    "(pip install 'astrocitizen[gui-web]'). "
                    "Use Ampliar/Browser para o mapa Leaflet."
                )
                hint.setObjectName("emptyState")
                hint.setWordWrap(True)
                hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
                web_l.addWidget(hint)
                self.stack.addWidget(self._web_page)
            root.addWidget(self.stack, 1)

            self.attr = QLabel("")
            self.attr.setWordWrap(True)
            self.attr.setTextFormat(Qt.TextFormat.RichText)
            root.addWidget(self.attr)

            self.stack.setCurrentIndex(0)

        def set_location(
            self,
            *,
            latitude_deg: float,
            longitude_deg: float,
            site_name: str = "",
            zoom: int = 6,
        ) -> None:
            self._lat = float(latitude_deg)
            self._lon = float(longitude_deg)
            self._site_name = site_name or ""
            self._zoom = max(1, min(int(zoom), 12))
            self._reload_map()

        def set_snapshot(
            self,
            image_path: str | Path | None,
            *,
            attribution: str = "",
            meta_line: str = "",
        ) -> None:
            path = Path(image_path) if image_path else None
            if path is None or not path.is_file():
                self.radar_label.setPixmap(QPixmap())
                self.radar_label.setText("Falha ao carregar PNG do radar")
            else:
                pix = QPixmap(str(path))
                if pix.isNull():
                    self.radar_label.setText("Falha ao carregar PNG do radar")
                else:
                    scaled = pix.scaled(
                        max(self.radar_label.width(), 320),
                        max(self.radar_label.height(), 200),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    self.radar_label.setPixmap(scaled)
            bits = [attribution] if attribution else []
            if meta_line:
                bits.append(f"<small>{meta_line}</small>")
            self.attr.setText("<br>".join(bits))
            # Prefer interactive map when WebEngine is ready and location known
            if self._view is not None and self._lat is not None:
                self.stack.setCurrentIndex(1)
            else:
                self.stack.setCurrentIndex(0)

        def _ensure_html(self) -> Path | None:
            if self._lat is None or self._lon is None:
                return None
            if self._html_path is None:
                tmp = Path(tempfile.gettempdir()) / "astrocitizen_radar_map.html"
                self._html_path = tmp
            return write_radar_map_html(
                self._html_path,
                latitude_deg=self._lat,
                longitude_deg=self._lon,
                zoom=self._zoom,
                site_name=self._site_name,
            )

        def _reload_map(self) -> None:
            path = self._ensure_html()
            if path is None:
                return
            if self._view is not None:
                self._view.load(QUrl.fromLocalFile(str(path)))
                self.stack.setCurrentIndex(1)

        def open_in_browser(self) -> None:
            path = self._ensure_html()
            if path is None:
                self.attr.setText("Sem coordenadas do observatorio.")
                return
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

        def open_modal(self) -> None:
            if self._lat is None or self._lon is None:
                self.attr.setText("Sem coordenadas do observatorio.")
                return
            dlg = RadarMapDialog(
                self,
                latitude_deg=self._lat,
                longitude_deg=self._lon,
                site_name=self._site_name,
                zoom=self._zoom,
                snapshot_path=None,
            )
            dlg.exec()

    class RadarMapDialog(QDialog):
        def __init__(
            self,
            parent: QWidget | None = None,
            *,
            latitude_deg: float,
            longitude_deg: float,
            site_name: str = "",
            zoom: int = 6,
            snapshot_path: str | Path | None = None,
        ) -> None:
            super().__init__(parent)
            self.setWindowTitle(f"Radar — {site_name or 'Observatorio'}")
            self.resize(960, 720)
            self.setModal(True)
            lay = QVBoxLayout(self)
            viewer = RadarMapViewer(self)
            # Hide nested Ampliar to avoid recursion noise; keep Browser.
            viewer.btn_modal.setVisible(False)
            viewer.set_location(
                latitude_deg=latitude_deg,
                longitude_deg=longitude_deg,
                site_name=site_name,
                zoom=zoom,
            )
            if snapshot_path:
                viewer.set_snapshot(snapshot_path)
            lay.addWidget(viewer, 1)
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            buttons.rejected.connect(self.reject)
            buttons.accepted.connect(self.accept)
            buttons.button(QDialogButtonBox.StandardButton.Close).clicked.connect(
                self.accept
            )
            lay.addWidget(buttons)

    return RadarMapViewer


__all__ = ["build_radar_map_viewer"]
