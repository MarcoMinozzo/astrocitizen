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
    site_name: str | None = None,
    latitude_deg: float | None = None,
    longitude_deg: float | None = None,
    elevation_m: float | None = None,
) -> list[str]:
    status = "VIABLE" if ok else "INVIABLE"
    req_lat = fc.get("request_latitude_deg", latitude_deg)
    req_lon = fc.get("request_longitude_deg", longitude_deg)
    api_lat = fc.get("api_latitude_deg")
    api_lon = fc.get("api_longitude_deg")
    lines = [
        f"status={status}",
    ]
    if site_name:
        lines.append(f"site={site_name}")
    if req_lat is not None and req_lon is not None:
        elev = f"  elev={elevation_m:.0f}m" if elevation_m is not None else ""
        lines.append(f"coords={float(req_lat):.5f},{float(req_lon):.5f}{elev}")
    if api_lat is not None and api_lon is not None:
        lines.append(f"open_meteo_grid={float(api_lat):.5f},{float(api_lon):.5f}")
    lines.extend(
        [
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
            f"hours={len(fc.get('hourly') or [])}"
            + (
                f"  forecast_days={fc.get('forecast_days')}"
                if fc.get("forecast_days") is not None
                else ""
            ),
        ]
    )
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


def build_night_payload(
    *,
    site: Any,
    night_date: str,
    meteo: Any,
    artifacts_root: Path,
) -> dict[str, Any]:
    """Fetch forecast + radar (safe to run off UI thread; no SQLite)."""
    from astrocitizen.adapters.meteo import RainViewerRadar
    from astrocitizen.adapters.sky import AstropyEphemeris
    from astrocitizen.planning.meteo_rules import evaluate_meteo_window

    eph = AstropyEphemeris()
    night = eph.night_window(
        latitude_deg=site.latitude_deg,
        longitude_deg=site.longitude_deg,
        elevation_m=site.elevation_m,
        night_date=night_date,
        night_start_rule=site.night_start_rule,
    )
    fc = meteo.forecast(
        latitude_deg=site.latitude_deg,
        longitude_deg=site.longitude_deg,
        start_utc=night["start_utc"],
        end_utc=night["end_utc"],
        elevation_m=getattr(site, "elevation_m", None),
    )
    ok, reason = evaluate_meteo_window(fc, site.meteo_thresholds)
    out = Path(artifacts_root) / "radar" / f"{site.id}_gui.png"
    meta = RainViewerRadar().region_image(
        latitude_deg=site.latitude_deg,
        longitude_deg=site.longitude_deg,
        zoom=6,
        size=512,
        out_path=out,
    )
    return {
        "ok": ok,
        "reason": reason,
        "fc": fc,
        "night": night,
        "radar_meta": meta,
        "night_date": night_date,
        "site_id": site.id,
        "site_name": getattr(site, "name", ""),
        "latitude_deg": site.latitude_deg,
        "longitude_deg": site.longitude_deg,
        "elevation_m": getattr(site, "elevation_m", None),
        "summary_lines": forecast_summary_lines(
            fc,
            ok=ok,
            reason=reason,
            night_start=night["start_utc"],
            night_end=night["end_utc"],
            site_name=getattr(site, "name", None),
            latitude_deg=site.latitude_deg,
            longitude_deg=site.longitude_deg,
            elevation_m=getattr(site, "elevation_m", None),
        ),
        "hourly_rows": hourly_table_rows(fc),
    }


def build_night_dashboard(parent: Any | None = None) -> Any:
    """Devolve a classe NightDashboard (requer PySide6)."""
    from PySide6.QtCore import QDate, QObject, Qt, QThread, Signal
    from PySide6.QtGui import QPixmap
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QDateEdit,
        QFrame,
        QHBoxLayout,
        QLabel,
        QMessageBox,
        QPushButton,
        QScrollArea,
        QSlider,
        QSplitter,
        QTableWidget,
        QTableWidgetItem,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    from astrocitizen.adapters.meteo import ManualMeteo, OpenMeteo
    from astrocitizen.adapters.sky import AstropyEphemeris
    from astrocitizen.desktop.sky_chart import build_sky_chart_widget
    from astrocitizen.desktop.theme import viability_badge
    from astrocitizen.planning import GenerateDailyPlan
    from astrocitizen.planning.sky_projection import (
        clamp_utc_to_night,
        interpolate_night_utc,
        load_sky_chart_from_archive,
        night_fraction_for_utc,
        now_utc_iso,
    )
    from astrocitizen.shared.paths import default_artifacts_root

    class _NightWorker(QObject):
        finished = Signal(dict)
        failed = Signal(str)

        def __init__(
            self,
            *,
            site: Any,
            night_date: str,
            meteo: Any,
            artifacts_root: Path,
        ) -> None:
            super().__init__()
            self._site = site
            self._night_date = night_date
            self._meteo = meteo
            self._artifacts_root = artifacts_root

        def run(self) -> None:
            try:
                payload = build_night_payload(
                    site=self._site,
                    night_date=self._night_date,
                    meteo=self._meteo,
                    artifacts_root=self._artifacts_root,
                )
                self.finished.emit(payload)
            except Exception as exc:  # noqa: BLE001 - worker boundary
                self.failed.emit(str(exc))

    class NightDashboard(QWidget):
        def __init__(self, archive: Any, *, artifacts_root: Path | None = None) -> None:
            super().__init__(parent)
            self.archive = archive
            self.artifacts_root = Path(artifacts_root or default_artifacts_root())
            self._sites: list[Any] = []
            self._workspace_id: UUID | None = None
            self._thread: QThread | None = None
            self._worker: _NightWorker | None = None
            self._night_window: dict[str, str] | None = None
            self._sky_utc: str | None = None
            self._updating_slider = False
            self._eph = AstropyEphemeris()

            top = QHBoxLayout()
            self.site_combo = QComboBox()
            self.date_edit = QDateEdit()
            self.date_edit.setCalendarPopup(True)
            self.date_edit.setDisplayFormat("yyyy-MM-dd")
            self.date_edit.setDate(QDate.fromString(tonight_utc_date(), "yyyy-MM-dd"))
            self.meteo_combo = QComboBox()
            self.meteo_combo.addItem("Open-Meteo", "api")
            self.meteo_combo.addItem("Manual (limpo)", "manual")
            self.badge = QLabel("-")
            self.badge.setObjectName("badgeIdle")
            self.refresh_btn = QPushButton("Atualizar noite")
            self.refresh_btn.clicked.connect(self.refresh_night)
            self.plan_btn = QPushButton("Gerar plano")
            self.plan_btn.setObjectName("secondaryBtn")
            self.plan_btn.clicked.connect(self.generate_plan)
            top.addWidget(QLabel("Site"))
            top.addWidget(self.site_combo, 1)
            top.addWidget(QLabel("Noite"))
            top.addWidget(self.date_edit)
            top.addWidget(QLabel("Meteo"))
            top.addWidget(self.meteo_combo)
            top.addWidget(self.badge)
            top.addWidget(self.refresh_btn)
            top.addWidget(self.plan_btn)

            self.coords_label = QLabel("")
            self.coords_label.setObjectName("emptyState")
            self.coords_label.setWordWrap(True)

            self.summary = QTextEdit()
            self.summary.setReadOnly(True)
            self.summary.setMaximumHeight(140)

            self.hours = QTableWidget(0, 7)
            self.hours.setAlternatingRowColors(True)
            self.hours.setHorizontalHeaderLabels(
                ["UTC", "Cloud%", "Wind", "RH%", "DewC", "Precipmm", "Prob%"]
            )

            self.plan_label = QLabel("plano: -")
            self.plan_label.setWordWrap(True)

            SkyChartWidget = build_sky_chart_widget()
            self.sky_chart = SkyChartWidget()
            self.sky_chart.markerSelected.connect(self._on_sky_marker)
            self.sky_detail = QLabel(
                "Carta do plano (L0): alvos do diario + Sol/Lua — nao e planetario."
            )
            self.sky_detail.setObjectName("emptyState")
            self.sky_detail.setWordWrap(True)
            self.sky_time_label = QLabel("hora carta: -")
            self.sky_slider = QSlider(Qt.Orientation.Horizontal)
            self.sky_slider.setRange(0, 1000)
            self.sky_slider.setValue(0)
            self.sky_slider.setEnabled(False)
            self.sky_slider.valueChanged.connect(self._on_sky_slider)
            self.sky_now_btn = QPushButton("Agora")
            self.sky_now_btn.setObjectName("secondaryBtn")
            self.sky_now_btn.clicked.connect(self._sky_now)
            self.sky_stars = QCheckBox("Estrelas brilhantes")
            self.sky_stars.setChecked(True)
            self.sky_stars.setToolTip(
                "Catalogo leve (~50 estrelas; nao e planetario)"
            )
            self.sky_stars.toggled.connect(lambda _=None: self._refresh_sky_chart())
            sky_time_row = QHBoxLayout()
            sky_time_row.addWidget(self.sky_time_label, 1)
            sky_time_row.addWidget(self.sky_stars)
            sky_time_row.addWidget(self.sky_now_btn)

            self.radar_label = QLabel("Radar: clique Atualizar")
            self.radar_label.setObjectName("radarPane")
            self.radar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.radar_label.setMinimumSize(160, 100)
            self.radar_attr = QLabel("")
            self.radar_attr.setWordWrap(True)
            self.radar_attr.setTextFormat(Qt.TextFormat.RichText)

            left = QWidget()
            left_l = QVBoxLayout(left)
            left_l.addWidget(QLabel("Viabilidade / forecast"))
            left_l.addWidget(self.coords_label)
            left_l.addWidget(self.summary)
            left_l.addWidget(QLabel("Horario (janela da noite)"))
            left_l.addWidget(self.hours, 1)
            left_l.addWidget(self.plan_label)

            sky_pane = QWidget()
            sky_pane.setMinimumHeight(200)
            sky_l = QVBoxLayout(sky_pane)
            sky_l.setContentsMargins(0, 0, 0, 0)
            sky_l.addWidget(QLabel("Carta do plano"))
            sky_l.addWidget(self.sky_chart, 1)
            sky_l.addLayout(sky_time_row)
            sky_l.addWidget(self.sky_slider)
            sky_l.addWidget(self.sky_detail)

            radar_pane = QWidget()
            radar_l = QVBoxLayout(radar_pane)
            radar_l.setContentsMargins(0, 0, 0, 0)
            radar_l.addWidget(QLabel("Radar (RainViewer)"))
            radar_l.addWidget(self.radar_label, 1)
            radar_l.addWidget(self.radar_attr)

            right = QSplitter(Qt.Orientation.Vertical)
            right.addWidget(sky_pane)
            right.addWidget(radar_pane)
            right.setStretchFactor(0, 4)
            right.setStretchFactor(1, 1)
            right.setSizes([360, 140])
            self._right_split = right

            split = QSplitter()
            split.addWidget(left)
            split.addWidget(right)
            split.setStretchFactor(0, 2)
            split.setStretchFactor(1, 3)
            split.setSizes([400, 520])
            self._main_split = split

            content = QWidget()
            content_l = QVBoxLayout(content)
            content_l.setContentsMargins(0, 0, 0, 0)
            content_l.addWidget(split, 1)

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded
            )
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            scroll.setWidget(content)

            root = QVBoxLayout(self)
            root.setContentsMargins(16, 12, 16, 12)
            root.addLayout(top)
            root.addWidget(scroll, 1)

            self.site_combo.currentIndexChanged.connect(self._on_site_combo_changed)
            self._syncing_shell = False

        def _bootstrap_sky_chart(self) -> None:
            """Inicializa carta sem esperar meteo/radar (AC-079 UX)."""
            site = self._current_site()
            if site is None or self._workspace_id is None:
                return
            night_date = self.date_edit.date().toString("yyyy-MM-dd")
            try:
                night = self._eph.night_window(
                    latitude_deg=site.latitude_deg,
                    longitude_deg=site.longitude_deg,
                    elevation_m=site.elevation_m,
                    night_date=night_date,
                    night_start_rule=getattr(
                        site, "night_start_rule", "astronomical_twilight"
                    ),
                )
            except Exception as exc:  # noqa: BLE001
                self.sky_detail.setText(f"erro carta: {exc}")
                return
            self._init_sky_from_night(night)

        def _set_badge(self, ok: bool | None) -> None:
            label, name = viability_badge(ok)
            self.badge.setText(label)
            self.badge.setObjectName(name)
            # force stylesheet re-apply for objectName change
            self.badge.style().unpolish(self.badge)
            self.badge.style().polish(self.badge)

        def load_sites(self) -> None:
            self._syncing_shell = True
            cur = self.site_combo.currentData()
            self.site_combo.clear()
            self._sites = []
            workspaces = self.archive.list_workspaces()
            if not workspaces:
                self.summary.setPlainText("Sem workspace. Rode: astrocitizen init-db")
                self.coords_label.setText("")
                self._set_badge(None)
                self._syncing_shell = False
                return
            self._workspace_id = workspaces[0].id
            self._sites = self.archive.list_sites(self._workspace_id)
            for s in self._sites:
                mark = "*" if s.is_default else " "
                self.site_combo.addItem(
                    f"{mark} {s.name}  ({s.latitude_deg:.4f}, {s.longitude_deg:.4f})",
                    s.id,
                )
            if cur is not None:
                i = self.site_combo.findData(cur)
                if i >= 0:
                    self.site_combo.setCurrentIndex(i)
            if not self._sites:
                self.summary.setPlainText("Sem sites. Rode: astrocitizen site add ...")
                self.coords_label.setText("")
                self._set_badge(None)
            else:
                self._update_coords_label()
                self._bootstrap_sky_chart()
            self._syncing_shell = False

        def set_shell_context(
            self, *, site_id: object = None, program_id: object = None
        ) -> None:
            """Sync ContextBar site (RN-024: meteo do local de observacao)."""
            _ = program_id
            if site_id is None:
                return
            self._syncing_shell = True
            changed = False
            i = self.site_combo.findData(site_id)
            if i >= 0 and i != self.site_combo.currentIndex():
                self.site_combo.setCurrentIndex(i)
                changed = True
            self._syncing_shell = False
            self._update_coords_label()
            if changed and self._current_site() is not None:
                self._bootstrap_sky_chart()
                self.refresh_night()

        def set_shell_night_date(self, night_date: str) -> None:
            if not night_date:
                return
            qd = QDate.fromString(night_date, "yyyy-MM-dd")
            if qd.isValid():
                self.date_edit.setDate(qd)

        def _on_site_combo_changed(self, *_args: object) -> None:
            self._update_coords_label()
            if self._syncing_shell:
                return
            if self._current_site() is not None:
                self._bootstrap_sky_chart()
                self.refresh_night()

        def _update_coords_label(self) -> None:
            site = self._current_site()
            if site is None:
                self.coords_label.setText("Sem site — meteo requer lat/lon do observatorio.")
                return
            self.coords_label.setText(
                f"Observatorio: {site.name}  ·  "
                f"lat={site.latitude_deg:.5f}  lon={site.longitude_deg:.5f}  "
                f"elev={site.elevation_m:.0f} m  ·  tz={site.timezone}"
            )

        def _current_site(self) -> Any | None:
            sid = self.site_combo.currentData()
            if sid is None:
                return None
            # Sempre rele do arquivo (coords actualizadas apos editar Site)
            fresh = self.archive.get_site(sid)
            if fresh is not None:
                return fresh
            for s in self._sites:
                if s.id == sid:
                    return s
            return None

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

        def _on_sky_marker(self, marker: Any) -> None:
            if marker is None:
                self.sky_detail.setText(
                    "Carta do plano (L0): clique num alvo para detalhe."
                )
                return
            self.sky_detail.setText(
                f"{marker.label}  alt={marker.alt_deg:.1f}°  az={marker.az_deg:.1f}°  "
                f"estado={marker.state}"
                + (f"  status={marker.status}" if marker.status else "")
            )
            if marker.block_id is not None:
                self.plan_label.setText(
                    f"{self.plan_label.text()}  ·  seleccionado={marker.label}"
                )

        def _on_sky_slider(self, value: int) -> None:
            if self._updating_slider or not self._night_window:
                return
            frac = value / 1000.0
            self._sky_utc = interpolate_night_utc(
                self._night_window["start_utc"],
                self._night_window["end_utc"],
                frac,
            )
            self._refresh_sky_chart()

        def _sky_now(self) -> None:
            if not self._night_window:
                return
            utc = clamp_utc_to_night(
                now_utc_iso(),
                self._night_window["start_utc"],
                self._night_window["end_utc"],
            )
            self._sky_utc = utc
            frac = night_fraction_for_utc(
                self._night_window["start_utc"],
                self._night_window["end_utc"],
                utc,
            )
            self._updating_slider = True
            self.sky_slider.setValue(int(round(frac * 1000)))
            self._updating_slider = False
            self._refresh_sky_chart()

        def _refresh_sky_chart(self) -> None:
            site = self._current_site()
            if (
                site is None
                or self._workspace_id is None
                or not self._sky_utc
                or not self._night_window
            ):
                self.sky_chart.set_model(None)
                self.sky_time_label.setText("hora carta: -")
                return
            night_date = self.date_edit.date().toString("yyyy-MM-dd")
            try:
                model = load_sky_chart_from_archive(
                    self.archive,
                    workspace_id=self._workspace_id,
                    site=site,
                    night_date=night_date,
                    utc_iso=self._sky_utc,
                    ephemeris=self._eph,
                    night_window=self._night_window,
                    include_bright_stars=bool(self.sky_stars.isChecked()),
                )
            except Exception as exc:  # noqa: BLE001 - UI boundary
                self.sky_detail.setText(f"erro carta: {exc}")
                return
            self.sky_chart.set_model(model)
            self.sky_time_label.setText(f"hora carta: {self._sky_utc}")
            self.sky_detail.setText(model.status_line)

        def _init_sky_from_night(self, night: dict[str, str]) -> None:
            self._night_window = {
                "start_utc": night["start_utc"],
                "end_utc": night["end_utc"],
            }
            self.sky_slider.setEnabled(True)
            utc = clamp_utc_to_night(
                now_utc_iso(),
                night["start_utc"],
                night["end_utc"],
            )
            self._sky_utc = utc
            frac = night_fraction_for_utc(
                night["start_utc"], night["end_utc"], utc
            )
            self._updating_slider = True
            self.sky_slider.setValue(int(round(frac * 1000)))
            self._updating_slider = False
            self._refresh_sky_chart()

        def _set_busy(self, busy: bool) -> None:
            self.refresh_btn.setEnabled(not busy)
            self.plan_btn.setEnabled(not busy)
            self.site_combo.setEnabled(not busy)
            self.date_edit.setEnabled(not busy)
            self.meteo_combo.setEnabled(not busy)

        def refresh_night(self) -> None:
            site = self._current_site()
            if site is None or self._workspace_id is None:
                QMessageBox.warning(self, "Noite", "Nenhum site seleccionado.")
                return
            if self._thread is not None and self._thread.isRunning():
                return
            night_date = self.date_edit.date().toString("yyyy-MM-dd")
            self._set_busy(True)
            self._update_coords_label()
            self.summary.setPlainText(
                f"A carregar meteo para {site.name} "
                f"({site.latitude_deg:.4f}, {site.longitude_deg:.4f})..."
            )
            self._set_badge(None)

            thread = QThread(self)
            worker = _NightWorker(
                site=site,
                night_date=night_date,
                meteo=self._meteo(),
                artifacts_root=self.artifacts_root,
            )
            worker.moveToThread(thread)
            thread.started.connect(worker.run)
            worker.finished.connect(self._on_night_ok)
            worker.failed.connect(self._on_night_fail)
            worker.finished.connect(thread.quit)
            worker.failed.connect(thread.quit)
            thread.finished.connect(worker.deleteLater)
            thread.finished.connect(thread.deleteLater)
            thread.finished.connect(self._on_thread_done)
            self._thread = thread
            self._worker = worker
            thread.start()

        def _on_thread_done(self) -> None:
            self._thread = None
            self._worker = None
            self._set_busy(False)

        def _on_night_ok(self, payload: dict) -> None:
            self._set_badge(bool(payload.get("ok")))
            self.summary.setPlainText("\n".join(payload.get("summary_lines") or []))
            rows = payload.get("hourly_rows") or []
            self.hours.setRowCount(len(rows))
            for r, row in enumerate(rows):
                for c, val in enumerate(row):
                    self.hours.setItem(r, c, QTableWidgetItem(str(val)))
            self.hours.resizeColumnsToContents()
            site = self._current_site()
            night_date = str(payload.get("night_date") or "")
            if site is not None and night_date and self._workspace_id is not None:
                self._update_plan_label(site, night_date)
            else:
                self.plan_label.setText("plano: -")
            night = payload.get("night") or {}
            if night.get("start_utc") and night.get("end_utc"):
                self._init_sky_from_night(night)
            meta = payload.get("radar_meta") or {}
            pix = QPixmap(str(meta.get("image_path") or ""))
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
                f"<small>radar lat={meta.get('latitude_deg')} "
                f"lon={meta.get('longitude_deg')} · {meta.get('image_path')}</small>"
            )

        def _on_night_fail(self, message: str) -> None:
            self._set_badge(None)
            self.summary.setPlainText(f"erro: {message}")
            QMessageBox.critical(self, "Noite", message)

        def generate_plan(self) -> None:
            site = self._current_site()
            if site is None or self._workspace_id is None:
                QMessageBox.warning(self, "Noite", "Nenhum site seleccionado.")
                return
            night_date = self.date_edit.date().toString("yyyy-MM-dd")
            self._set_busy(True)
            try:
                plan = GenerateDailyPlan(
                    self.archive, AstropyEphemeris(), self._meteo()
                ).execute(
                    workspace_id=self._workspace_id,
                    site_id=site.id,
                    night_date=night_date,
                )
                self._update_plan_label(site, night_date)
                self._refresh_sky_chart()
                QMessageBox.information(
                    self,
                    "Plano",
                    f"Plano gerado: {plan.id}\nestado={plan.state}",
                )
            except Exception as exc:  # noqa: BLE001 - UI boundary
                QMessageBox.critical(self, "Gerar plano", str(exc))
            finally:
                self._set_busy(False)

    return NightDashboard
