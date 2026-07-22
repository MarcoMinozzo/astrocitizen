"""Simple XY plot widget (QPainter, sem matplotlib)."""

from __future__ import annotations

from typing import Any


def build_series_plot() -> type:
    from PySide6.QtCore import QPointF, QRectF, Qt
    from PySide6.QtGui import QColor, QPainter, QPen
    from PySide6.QtWidgets import QWidget

    from astrocitizen.desktop.theme import COLORS, NIGHT_VISION_COLORS, load_night_vision_pref

    class SeriesPlot(QWidget):
        def __init__(self, parent: QWidget | None = None) -> None:
            super().__init__(parent)
            self._xs: list[float] = []
            self._ys: list[float] = []
            self._title = ""
            self._xlabel = "x"
            self._ylabel = "y"
            self.setMinimumHeight(220)
            self.setObjectName("radarPane")

        def clear(self) -> None:
            self._xs, self._ys = [], []
            self._title = ""
            self.update()

        def set_series(
            self,
            xs: list[float],
            ys: list[float],
            *,
            title: str = "",
            xlabel: str = "x",
            ylabel: str = "y",
        ) -> None:
            self._xs = list(xs)
            self._ys = list(ys)
            self._title = title
            self._xlabel = xlabel
            self._ylabel = ylabel
            self.update()

        def _palette(self) -> dict[str, str]:
            try:
                nv = load_night_vision_pref()
            except Exception:  # noqa: BLE001
                nv = False
            return NIGHT_VISION_COLORS if nv else COLORS

        def paintEvent(self, event: Any) -> None:  # noqa: N802
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            c = self._palette()
            painter.fillRect(self.rect(), QColor(c["bg_elevated"]))
            margin = 44
            plot = QRectF(
                margin,
                28,
                max(10.0, self.width() - margin - 16),
                max(10.0, self.height() - margin - 20),
            )
            painter.setPen(QPen(QColor(c["border"]), 1))
            painter.drawRect(plot)
            painter.setPen(QColor(c["text_muted"]))
            if self._title:
                painter.drawText(
                    QRectF(8, 4, self.width() - 16, 20),
                    int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                    self._title,
                )
            if len(self._xs) < 2 or len(self._ys) < 2:
                painter.drawText(
                    plot,
                    int(Qt.AlignmentFlag.AlignCenter),
                    "Sem pontos para plot (>=2)",
                )
                return
            xmin, xmax = min(self._xs), max(self._xs)
            ymin, ymax = min(self._ys), max(self._ys)
            if xmax <= xmin:
                xmax = xmin + 1.0
            if ymax <= ymin:
                ymax = ymin + 1.0

            def map_pt(x: float, y: float) -> QPointF:
                px = plot.left() + (x - xmin) / (xmax - xmin) * plot.width()
                py = plot.bottom() - (y - ymin) / (ymax - ymin) * plot.height()
                return QPointF(px, py)

            pen = QPen(QColor(c["accent"]), 2)
            painter.setPen(pen)
            for i in range(1, len(self._xs)):
                painter.drawLine(
                    map_pt(self._xs[i - 1], self._ys[i - 1]),
                    map_pt(self._xs[i], self._ys[i]),
                )
            painter.setPen(QColor(c["text_muted"]))
            painter.drawText(
                QRectF(plot.left(), self.height() - 18, plot.width(), 16),
                int(Qt.AlignmentFlag.AlignCenter),
                f"{self._xlabel}  [{xmin:.4g} .. {xmax:.4g}]  ·  "
                f"{self._ylabel}  [{ymin:.4g} .. {ymax:.4g}]",
            )

    return SeriesPlot
