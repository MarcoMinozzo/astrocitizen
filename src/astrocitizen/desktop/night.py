"""Painel Noite: forecast Open-Meteo + radar RainViewer + plano diario."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID


def tonight_utc_date() -> str:
    """Data civil UTC da noite corrente."""
    return datetime.now(timezone.utc).date().isoformat()


def forecast_summary_lines(
    fc: dict[str, Any],
    *,
    ok: bool,
    reason: str | None,
    night_start: str,
    night_end: str,
) -> list[str]:
    status = "VIABLE" if ok else "INVIABLE"
    lines = [
        f"status={status}",
        f"window={night_start} .. {night_end}",
        (
            f"cloud_max={fc.get('cloud_cover_pct')}%  "
            f"wind_max={fc.get('wind_ms')} m/s  "
            f"rh_max={fc.get('humidity_pct')}%"
        ),
        (
            f"dew_margin_min={fc.get('dew_margin_c')} C  "
            f"precip={fc.get('precipitation')}  "
            f"prob_max={fc.get('precip_probability_pct')}%"
        ),
        f"hours={len(fc.get('hourly') or [])}",
    ]
    if reason:
        lines.append(f"reason={reason}")
    return lines


def hourly_table_rows(fc: dict[str, Any]) -> list[list[str]]:
    rows: list[list[str]] = []
    for h in fc.get("hourly") or []:
        rows.append(
            [
                str(h.get("time_utc") or ""),
                f"{h.get('cloud_cover_pct')}",
                f"{h.get('wind_ms')}",
                f"{h.get('humidity_pct')}",
                f"{h.get('dewpoint_c')}",
                f"{h.get('precipitation_mm')}",
                f"{h.get('precip_probability_pct')}",
            ]
        )
    return rows


def plan_status_text(plan: Any | None, blocks: list[Any]) -> str:
    if plan is None:
        return "plano: nenhum gerado para esta noite/site"
    counts: dict[str, int] = {}
    for b in blocks:
        st = getattr(b, "status", None) or "?"
        counts[st] = counts.get(st, 0) + 1
    parts = [f"{k}={v}" for k, v in sorted(counts.items())]
    return (
        f"plano={plan.state}  id={str(plan.id)[:8]}  "
        f"blocks={len(blocks)}"
        + (f"  ({', '.join(parts)})" if parts else "")
    )


def fetch_plan_status(
    archive: Any, workspace_id: UUID, site_id: UUID, night_date: str
) -> str:
    plan = archive.get_daily_plan_for_night(workspace_id, site_id, night_date)
    blocks = archive.list_observation_blocks(plan.id) if plan is not None else []
    return plan_status_text(plan, blocks)


def build_night_dashboard(parent: Any | None = None) -> Any:
    """Devolve a classe NightDashboard (requer PySide6)."""
    from PySide6.QtCore import QDate, Qt
    from PySide6.QtGui import QPixmap
    from PySide6.QtWidgets import (
        QComboBox,
        QDateEdit,
        QHBoxLayout,
        QLabel,
        QMessageBox,
        QPushButton,
        QSplitter,
        QTableWidget,
        QTableWidgetItem,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    from astrocitizen.adapters.meteo import ManualMeteo, OpenMeteo, RainViewerRadar
    from astrocitizen.adapters.sky import AstropyEphemeris
    from astrocitizen.planning import GenerateDailyPlan
    from astrocitizen.planning.meteo_rules import evaluate_meteo_window
    from astrocitizen.shared.paths import default_artifacts_root

    class NightDashboard(QWidget):
        def __init__(self, archive: Any, *, artifacts_root: Path | None = None) -> None:
            super().__init__(parent)
            self.archive = archive
            self.artifacts_root = Path(artifacts_root or default_artifacts_root())
            self._sites: list[Any] = []
            self._workspace_id: UUID | None = None

            top = QHBoxLayout()
            self.site_combo = QComboBox()
            self.date_edit = QDateEdit()
            self.date_edit.setCalendarPopup(True)
            self.date_edit.setDisplayFormat("yyyy-MM-dd")
            self.date_edit.setDate(QDate.fromString(tonight_utc_date(), "yyyy-MM-dd"))
            self.meteo_combo = QComboBox()
            self.meteo_combo.addItem("Open-Meteo", "api")
            self.meteo_combo.addItem("Manual (limpo)", "manual")
            self.refresh_btn = QPushButton("Atualizar noite")
            self.refresh_btn.clicked.connect(self.refresh_night)
            self.plan_btn = QPushButton("Gerar plano")
            self.plan_btn.clicked.connect(self.generate_plan)
            top.addWidget(QLabel("Site"))
            top.addWidget(self.site_combo, 1)
            top.addWidget(QLabel("Noite"))
            top.addWidget(self.date_edit)
            top.addWidget(QLabel("Meteo"))
            top.addWidget(self.meteo_combo)
            top.addWidget(self.refresh_btn)
            top.addWidget(self.plan_btn)

            self.summary = QTextEdit()
            self.summary.setReadOnly(True)
            self.summary.setMaximumHeight(120)

            self.hours = QTableWidget(0, 7)
            self.hours.setHorizontalHeaderLabels(
                ["UTC", "Cloud%", "Wind", "RH%", "DewC", "Precipmm", "Prob%"]
            )

            self.plan_label = QLabel("plano: -")
            self.plan_label.setWordWrap(True)

            self.radar_label = QLabel("Radar: clique Atualizar")
            self.radar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.radar_label.setMinimumSize(320, 320)
            self.radar_label.setStyleSheet("background:#111; color:#aaa;")
            self.radar_attr = QLabel("")
            self.radar_attr.setWordWrap(True)
            self.radar_attr.setTextFormat(Qt.TextFormat.RichText)

            left = QWidget()
            left_l = QVBoxLayout(left)
            left_l.addWidget(QLabel("Viabilidade / forecast"))
            left_l.addWidget(self.summary)
            left_l.addWidget(QLabel("Horario (janela da noite)"))
            left_l.addWidget(self.hours, 1)
            left_l.addWidget(self.plan_label)

            right = QWidget()
            right_l = QVBoxLayout(right)
            right_l.addWidget(QLabel("Radar (RainViewer)"))
            right_l.addWidget(self.radar_label, 1)
            right_l.addWidget(self.radar_attr)

            split = QSplitter()
            split.addWidget(left)
            split.addWidget(right)
            split.setStretchFactor(0, 3)
            split.setStretchFactor(1, 2)

            root = QVBoxLayout(self)
            root.addLayout(top)
            root.addWidget(split, 1)

        def load_sites(self) -> None:
            self.site_combo.clear()
            self._sites = []
            workspaces = self.archive.list_workspaces()
            if not workspaces:
                self.summary.setPlainText("Sem workspace. Rode: astrocitizen init-db")
                return
            self._workspace_id = workspaces[0].id
            self._sites = self.archive.list_sites(self._workspace_id)
            for s in self._sites:
                mark = "*" if s.is_default else " "
                self.site_combo.addItem(f"{mark} {s.name}", s.id)
            if not self._sites:
                self.summary.setPlainText("Sem sites. Rode: astrocitizen site add ...")

        def _current_site(self) -> Any | None:
            idx = self.site_combo.currentIndex()
            if idx < 0 or idx >= len(self._sites):
                return None
            return self._sites[idx]

        def _meteo(self) -> Any:
            if self.meteo_combo.currentData() == "manual":
                return ManualMeteo(
                    cloud_cover_pct=10.0,
                    wind_ms=2.0,
                    humidity_pct=40.0,
                    precipitation=False,
                )
            return OpenMeteo()

        def _update_plan_label(self, site: Any, night_date: str) -> None:
            assert self._workspace_id is not None
            self.plan_label.setText(
                fetch_plan_status(self.archive, self._workspace_id, site.id, night_date)
            )

        def refresh_night(self) -> None:
            site = self._current_site()
            if site is None or self._workspace_id is None:
                QMessageBox.warning(self, "Noite", "Nenhum site seleccionado.")
                return
            night_date = self.date_edit.date().toString("yyyy-MM-dd")
            self.refresh_btn.setEnabled(False)
            self.plan_btn.setEnabled(False)
            self.summary.setPlainText("A carregar Open-Meteo + radar...")
            try:
                eph = AstropyEphemeris()
                night = eph.night_window(
                    latitude_deg=site.latitude_deg,
                    longitude_deg=site.longitude_deg,
                    elevation_m=site.elevation_m,
                    night_date=night_date,
                    night_start_rule=site.night_start_rule,
                )
                fc = self._meteo().forecast(
                    latitude_deg=site.latitude_deg,
                    longitude_deg=site.longitude_deg,
                    start_utc=night["start_utc"],
                    end_utc=night["end_utc"],
                )
                ok, reason = evaluate_meteo_window(fc, site.meteo_thresholds)
                self.summary.setPlainText(
                    "\n".join(
                        forecast_summary_lines(
                            fc,
                            ok=ok,
                            reason=reason,
                            night_start=night["start_utc"],
                            night_end=night["end_utc"],
                        )
                    )
                )
                rows = hourly_table_rows(fc)
                self.hours.setRowCount(len(rows))
                for r, row in enumerate(rows):
                    for c, val in enumerate(row):
                        self.hours.setItem(r, c, QTableWidgetItem(val))
                self.hours.resizeColumnsToContents()
                self._update_plan_label(site, night_date)

                out = self.artifacts_root / "radar" / f"{site.id}_gui.png"
                meta = RainViewerRadar().region_image(
                    latitude_deg=site.latitude_deg,
                    longitude_deg=site.longitude_deg,
                    zoom=6,
                    size=512,
                    out_path=out,
                )
                pix = QPixmap(str(meta["image_path"]))
                if pix.isNull():
                    self.radar_label.setText("Falha ao carregar PNG do radar")
                else:
                    scaled = pix.scaled(
                        max(self.radar_label.width(), 320),
                        max(self.radar_label.height(), 320),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    self.radar_label.setPixmap(scaled)
                self.radar_attr.setText(
                    f"{meta.get('attribution', '')}<br>"
                    f"<small>{meta.get('image_path')}</small>"
                )
            except Exception as exc:  # noqa: BLE001 - UI boundary
                self.summary.setPlainText(f"erro: {exc}")
                QMessageBox.critical(self, "Noite", str(exc))
            finally:
                self.refresh_btn.setEnabled(True)
                self.plan_btn.setEnabled(True)

        def generate_plan(self) -> None:
            site = self._current_site()
            if site is None or self._workspace_id is None:
                QMessageBox.warning(self, "Noite", "Nenhum site seleccionado.")
                return
            night_date = self.date_edit.date().toString("yyyy-MM-dd")
            self.plan_btn.setEnabled(False)
            self.refresh_btn.setEnabled(False)
            try:
                plan = GenerateDailyPlan(
                    self.archive, AstropyEphemeris(), self._meteo()
                ).execute(
                    workspace_id=self._workspace_id,
                    site_id=site.id,
                    night_date=night_date,
                )
                self._update_plan_label(site, night_date)
                QMessageBox.information(
                    self,
                    "Plano",
                    f"Plano gerado: {plan.id}\nestado={plan.state}",
                )
            except Exception as exc:  # noqa: BLE001 - UI boundary
                QMessageBox.critical(self, "Gerar plano", str(exc))
            finally:
                self.plan_btn.setEnabled(True)
                self.refresh_btn.setEnabled(True)

    return NightDashboard
