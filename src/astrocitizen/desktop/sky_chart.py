"""Widget Qt: carta do plano (AC-079 L0) — sem catalogo / planetario."""

from __future__ import annotations

import math
from typing import Any
from uuid import UUID

from astrocitizen.planning.sky_projection import SkyChartModel, SkyMarker


def build_sky_chart_widget(parent: Any | None = None) -> Any:
    from PySide6.QtCore import QPointF, Qt, Signal
    from PySide6.QtGui import QColor, QFont, QPainter, QPen
    from PySide6.QtWidgets import QSizePolicy, QWidget

    from astrocitizen.desktop.theme import COLORS

    STATE_COLORS = {
        "above": QColor(COLORS["ok"]),
        "below_threshold": QColor(COLORS["warn"]),
        "below_horizon": QColor(COLORS["text_muted"]),
        "inviavel_ceu": QColor(COLORS["bad"]),
        "body": QColor(COLORS["accent"]),
    }

    class SkyChartWidget(QWidget):
        markerSelected = Signal(object)  # SkyMarker | None

        def __init__(self) -> None:
            super().__init__(parent)
            self.setMinimumSize(280, 280)
            self.setObjectName("skyChart")
            self._model: SkyChartModel | None = None
            self._selected_block_id: UUID | None = None
            self._hit: list[tuple[float, float, SkyMarker]] = []
            self.setMouseTracking(True)
            self.setToolTip("Carta do plano (L0) — nao e um planetario")
            self.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )

        def set_model(self, model: SkyChartModel | None) -> None:
            self._model = model
            self.update()

        def set_selected_block_id(self, block_id: UUID | None) -> None:
            self._selected_block_id = block_id
            self.update()

        def _geom(self) -> tuple[float, float, float]:
            w, h = self.width(), self.height()
            margin = 28.0
            cx, cy = w / 2.0, h / 2.0
            radius = max(40.0, min(w, h) / 2.0 - margin)
            return cx, cy, radius

        def _to_pixel(self, x: float, y: float) -> QPointF:
            cx, cy, radius = self._geom()
            # y screen down; chart y is north-up
            return QPointF(cx + x * radius, cy - y * radius)

        def paintEvent(self, event: Any) -> None:  # noqa: N802
            _ = event
            p = QPainter(self)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            c = COLORS
            p.fillRect(self.rect(), QColor(c["radar"]))
            cx, cy, radius = self._geom()

            # Horizon disk
            p.setPen(QPen(QColor(c["border"]), 2))
            p.setBrush(QColor(c["bg_elevated"]))
            p.drawEllipse(QPointF(cx, cy), radius, radius)

            # Altitude rings 60/30
            p.setBrush(Qt.BrushStyle.NoBrush)
            for alt in (60.0, 30.0):
                r = radius * ((90.0 - alt) / 90.0)
                p.setPen(QPen(QColor(c["border"]), 1, Qt.PenStyle.DotLine))
                p.drawEllipse(QPointF(cx, cy), r, r)

            # Min-alt ring
            if self._model is not None:
                rmin = radius * self._model.min_alt_radius
                p.setPen(QPen(QColor(c["warn"]), 1.5, Qt.PenStyle.DashLine))
                p.drawEllipse(QPointF(cx, cy), rmin, rmin)

            # Cardinals
            font = QFont(self.font())
            font.setPointSize(max(8, font.pointSize()))
            p.setFont(font)
            p.setPen(QColor(c["text_muted"]))
            p.drawText(int(cx - 6), int(cy - radius - 6), "N")
            p.drawText(int(cx - 6), int(cy + radius + 16), "S")
            p.drawText(int(cx + radius + 4), int(cy + 4), "E")
            p.drawText(int(cx - radius - 14), int(cy + 4), "W")

            self._hit = []
            if self._model is None:
                p.setPen(QColor(c["text_muted"]))
                p.drawText(
                    self.rect(),
                    int(Qt.AlignmentFlag.AlignCenter),
                    "Sem dados — atualize a noite",
                )
                p.end()
                return

            for m in self._model.markers:
                if m.x is None or m.y is None:
                    continue
                pt = self._to_pixel(m.x, m.y)
                self._hit.append((pt.x(), pt.y(), m))
                color = STATE_COLORS.get(m.state, QColor(c["text"]))
                selected = (
                    m.block_id is not None
                    and m.block_id == self._selected_block_id
                )
                below = m.alt_deg < 0.0 or m.state == "below_horizon"
                size = 7.0 if m.kind == "target" else 9.0
                if m.kind == "sun":
                    col = QColor(c["accent"])
                    if below:
                        col.setAlpha(110)
                    p.setBrush(col)
                    p.setPen(QPen(QColor(c["text_muted"] if below else c["text"]), 1))
                    p.drawEllipse(pt, size, size)
                elif m.kind == "moon":
                    col = QColor("#c8d0dc")
                    if below:
                        col.setAlpha(110)
                    p.setBrush(col)
                    p.setPen(QPen(QColor(c["text_muted"]), 1))
                    p.drawEllipse(pt, size - 1, size - 1)
                else:
                    if below:
                        color.setAlpha(120)
                    p.setBrush(color)
                    pen = QPen(
                        QColor(c["text"]) if selected else color,
                        2 if selected else 1,
                    )
                    p.setPen(pen)
                    p.drawEllipse(pt, size, size)
                p.setPen(QColor(c["text_muted"] if below else c["text"]))
                p.drawText(int(pt.x() + 8), int(pt.y() - 4), m.label[:18])

            # Caption + hint
            p.setPen(QColor(c["text_muted"]))
            caption = f"Carta do plano · {self._model.utc_iso}"
            if self._model.site_name:
                caption = f"{self._model.site_name} · {caption}"
            p.drawText(8, self.height() - 8, caption)
            if self._model.n_targets == 0:
                p.setPen(QColor(c["warn"]))
                p.drawText(
                    8,
                    18,
                    "Sem alvos no plano — Gerar plano (com alvos)",
                )
            p.end()

        def mousePressEvent(self, event: Any) -> None:  # noqa: N802
            if event.button() != Qt.MouseButton.LeftButton:
                return
            pos = event.position()
            best: SkyMarker | None = None
            best_d = 14.0
            for x, y, m in self._hit:
                if m.kind != "target":
                    continue
                d = math.hypot(pos.x() - x, pos.y() - y)
                if d < best_d:
                    best_d = d
                    best = m
            if best is not None:
                self._selected_block_id = best.block_id
                self.update()
                self.markerSelected.emit(best)
            else:
                self.markerSelected.emit(None)

    return SkyChartWidget
