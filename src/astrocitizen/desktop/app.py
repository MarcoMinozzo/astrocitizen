"""Shell GUI PySide6 — IA 7 areas (U1) + ContextBar (U0)."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any


def run_gui(db_path: str | None = None) -> int:
    try:
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QKeySequence, QShortcut
        from PySide6.QtWidgets import (
            QApplication,
            QFrame,
            QHBoxLayout,
            QLabel,
            QListWidget,
            QListWidgetItem,
            QMainWindow,
            QPushButton,
            QStackedWidget,
            QStatusBar,
            QTableWidget,
            QTableWidgetItem,
            QVBoxLayout,
            QWidget,
        )
    except ImportError:
        print(
            "PySide6 nao instalado. Use: pip install 'astrocitizen[gui]'",
            file=sys.stderr,
        )
        return 1

    from astrocitizen.adapters.sqlite import SqliteArchive
    from astrocitizen.desktop.analyze_panel import build_analyze_dashboard
    from astrocitizen.desktop.archive_panel import build_archive_dashboard
    from astrocitizen.desktop.aavso_campaigns_browser import (
        build_aavso_campaigns_browser,
    )
    from astrocitizen.desktop.catalog_panel import build_catalog_dashboard
    from astrocitizen.desktop.contribute import build_contribute_dashboard
    from astrocitizen.desktop.entities import (
        build_programs_page,
        build_sites_page,
        build_targets_page,
    )
    from astrocitizen.desktop.equipment import build_equipment_page
    from astrocitizen.desktop.help_panel import area_to_help_topic, build_help_panel
    from astrocitizen.desktop.import_panel import build_import_dashboard
    from astrocitizen.desktop.night import build_night_dashboard
    from astrocitizen.desktop.observe_panel import build_observe_dashboard
    from astrocitizen.desktop.prefs_panel import build_prefs_panel
    from astrocitizen.desktop.program_active_panel import build_program_active_dashboard
    from astrocitizen.desktop.radio_panel import build_radio_dashboard
    from astrocitizen.desktop.session_panel import build_session_dashboard
    from astrocitizen.desktop.specialty_panel import build_specialty_dashboard
    from astrocitizen.desktop.theme import (
        apply_theme,
        empty_state_text,
        load_night_vision_pref,
        load_ui_lang_pref,
        save_night_vision_pref,
    )
    from astrocitizen.desktop.timing_panel import build_timing_dashboard
    from astrocitizen.desktop.widgets import build_shared_widgets
    from astrocitizen.shared.i18n import (
        detect_system_lang,
        resolve_ui_lang,
        set_current_lang,
        t,
    )
    from astrocitizen.shared.paths import default_artifacts_root, default_db_path

    NightDashboard = build_night_dashboard()
    ContributeDashboard = build_contribute_dashboard()
    ImportDashboard = build_import_dashboard()
    ArchiveDashboard = build_archive_dashboard()
    CatalogDashboard = build_catalog_dashboard()
    AnalyzeDashboard = build_analyze_dashboard()
    SitesPage = build_sites_page()
    ProgramsPage = build_programs_page()
    TargetsPage = build_targets_page()
    EquipmentPage = build_equipment_page()
    SessionDashboard = build_session_dashboard()
    ObserveDashboard = build_observe_dashboard()
    TimingDashboard = build_timing_dashboard()
    RadioDashboard = build_radio_dashboard()
    SpecialtyDashboard = build_specialty_dashboard()
    ProgramActiveDashboard = build_program_active_dashboard()
    AavsoCampaignsBrowser = build_aavso_campaigns_browser()
    HelpPanel = build_help_panel()
    PrefsPanel = build_prefs_panel()
    Shared = build_shared_widgets()
    ContextBar = Shared["ContextBar"]
    TabHub = Shared["TabHub"]

    # Stable nav keys (labels via t("nav.<key>"))
    NAV_KEYS: list[str] = [
        "Noite",
        "Observatorio",
        "Catalogo",
        "Analisar",
        "Contribuir",
        "Arquivo",
        "Configurar",
    ]
    class MainWindow(QMainWindow):
        def __init__(self, archive: SqliteArchive, db: Path) -> None:
            super().__init__()
            self.archive = archive
            self.db_path = db
            self.setWindowTitle("AstroCitizen")
            self.setMinimumSize(720, 520)
            self._fit_to_available_screen()

            outer = QWidget()
            outer_l = QVBoxLayout(outer)
            outer_l.setContentsMargins(0, 0, 0, 0)
            outer_l.setSpacing(0)

            brand = QFrame()
            brand.setObjectName("brandBar")
            brand_row = QHBoxLayout(brand)
            brand_row.setContentsMargins(16, 10, 16, 10)
            brand_row.setSpacing(12)
            brand_text = QVBoxLayout()
            brand_text.setContentsMargins(0, 0, 0, 0)
            brand_text.setSpacing(2)
            title = QLabel("AstroCitizen")
            title.setObjectName("brandTitle")
            self.brand_sub = QLabel()
            self.brand_sub.setObjectName("brandSubtitle")
            brand_text.addWidget(title)
            brand_text.addWidget(self.brand_sub)
            brand_row.addLayout(brand_text, 1)
            self.help_btn = QPushButton()
            self.help_btn.setObjectName("secondaryBtn")
            self.help_btn.clicked.connect(self._open_help)
            brand_row.addWidget(self.help_btn, 0, Qt.AlignmentFlag.AlignRight)
            self.nv_btn = QPushButton()
            self.nv_btn.setObjectName("nightVisionBtn")
            self.nv_btn.setCheckable(True)
            self.nv_btn.setToolTip(
                "Tema vermelho para preservar a adaptacao a escuridao "
                "(como em softwares observacionais)."
            )
            self.nv_btn.toggled.connect(self._on_night_vision)
            brand_row.addWidget(self.nv_btn, 0, Qt.AlignmentFlag.AlignRight)
            outer_l.addWidget(brand)

            self.context = ContextBar()
            outer_l.addWidget(self.context)
            self._night_vision = False
            self._app = QApplication.instance()

            body = QWidget()
            layout = QHBoxLayout(body)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)

            self.nav = QListWidget()
            self.nav.setObjectName("navList")
            self.nav.setFixedWidth(188)
            self.nav_names = list(NAV_KEYS)
            for _key in NAV_KEYS:
                QListWidgetItem("", self.nav)

            self.stack = QStackedWidget()
            layout.addWidget(self.nav)
            layout.addWidget(self.stack, 1)
            outer_l.addWidget(body, 1)
            self.setCentralWidget(outer)

            status = QStatusBar()
            self.setStatusBar(status)
            self._status = status
            status.showMessage(f"db={db}")

            arts = default_artifacts_root()
            on_ch = self._on_entities_changed

            self.night = NightDashboard(archive, artifacts_root=arts)
            self.contribute = ContributeDashboard(archive, artifacts_root=arts)
            self.import_panel = ImportDashboard(archive, artifacts_root=arts)
            self.sites_page = SitesPage(archive, on_changed=on_ch)
            self.programs_page = ProgramsPage(archive, on_changed=on_ch)
            self.targets_page = TargetsPage(archive, on_changed=on_ch)
            self.equipment_page = EquipmentPage(archive, on_changed=on_ch)
            self.session_panel = SessionDashboard(
                archive, artifacts_root=arts, on_changed=on_ch
            )
            self.observe_panel = ObserveDashboard(
                archive, artifacts_root=arts, on_changed=on_ch
            )
            self.timing_panel = TimingDashboard(
                archive, artifacts_root=arts, on_changed=on_ch
            )
            self.radio_panel = RadioDashboard(
                archive, artifacts_root=arts, on_changed=on_ch
            )
            self.specialty_panel = SpecialtyDashboard(
                archive, artifacts_root=arts, on_changed=on_ch
            )
            self.archive_panel = ArchiveDashboard(
                archive,
                artifacts_root=arts,
                on_changed=on_ch,
                on_contribute=lambda network=None, product_id=None: self._navigate_to(
                    "Contribuir", network=network, product_id=product_id
                ),
            )
            self.catalog_panel = CatalogDashboard(archive)
            self.analyze_panel = AnalyzeDashboard(
                archive, artifacts_root=arts, on_changed=on_ch
            )
            self.program_active = ProgramActiveDashboard(
                archive,
                on_navigate=self._navigate_to,
                on_changed=on_ch,
            )
            self.aavso_campaigns = AavsoCampaignsBrowser()
            self.help_panel = HelpPanel(archive=archive)
            self.prefs_panel = PrefsPanel(on_language_changed=self._on_language_changed)

            self.pages: dict[str, QWidget] = {}
            plan_page = self._table_page()
            self.pages["Plano diario"] = plan_page

            ser_hint = self._placeholder_page(
                "Video / SER",
                "Video de ocultacao: Observatorio → Timing (anexar SER/AVI + LC). "
                "Cubos speckle: tab Especialidades neste hub Importar. "
                "CLI: observe occultation --video · import speckle.",
            )

            # U2: Import hub = todos os canais IN-* de ficheiro
            self.import_hub = TabHub(
                title="",
                tabs=[
                    ("FITS", self.import_panel),
                    ("Radio", self.radio_panel),
                    ("Especialidades", self.specialty_panel),
                    ("Video / SER", ser_hint),
                ],
            )

            # Noite = meteo + planos embutidos
            self.noite_hub = TabHub(
                title="",
                tabs=[
                    ("Meteo / carta", self.night),
                    ("Planos", plan_page),
                ],
            )

            self.observatorio = TabHub(
                title="Observatorio",
                hint="Programa activo, sessao, importacao e canais da noite.",
                tabs=[
                    ("Programa", self.program_active),
                    ("Campanhas AAVSO", self.aavso_campaigns),
                    ("Sessao", self.session_panel),
                    ("Importar", self.import_hub),
                    ("Observar", self.observe_panel),
                    ("Timing", self.timing_panel),
                ],
            )

            self.configurar = TabHub(
                title="Configurar",
                hint="Metadados do observatorio (RN-001+).",
                tabs=[
                    ("Sites", self.sites_page),
                    ("Equipamento", self.equipment_page),
                    ("Programas", self.programs_page),
                    ("Alvos", self.targets_page),
                    ("Preferencias", self.prefs_panel),
                    ("Ajuda", self.help_panel),
                ],
            )

            # Stack = 7 areas
            self.stack.addWidget(self.noite_hub)  # 0 Noite
            self.stack.addWidget(self.observatorio)  # 1 Observatorio
            self.stack.addWidget(self.catalog_panel)  # 2 Catalogo
            self.stack.addWidget(self.analyze_panel)  # 3 Analisar
            self.stack.addWidget(self.contribute)  # 4 Contribuir
            self.stack.addWidget(self.archive_panel)  # 5 Arquivo
            self.stack.addWidget(self.configurar)  # 6 Configurar

            self.nav.currentRowChanged.connect(self._on_nav)
            self.nav.setCurrentRow(0)
            self.context.site_changed.connect(self._on_shell_site)
            self.context.program_changed.connect(self._on_shell_program)
            self.context.night_date_changed.connect(self._on_shell_night_date)
            QShortcut(QKeySequence("F1"), self, activated=self._open_help)
            # Preferencia visao noturna (apos widgets criados)
            if load_night_vision_pref():
                self.nv_btn.blockSignals(True)
                self.nv_btn.setChecked(True)
                self.nv_btn.blockSignals(False)
                self._apply_night_vision(True)
            self._retranslate_shell()
            self.refresh()

        def _on_language_changed(self, _lang: str) -> None:
            self._retranslate_shell()

        def _retranslate_shell(self) -> None:
            self.brand_sub.setText(t("brand.subtitle"))
            self.help_btn.setText(t("btn.help"))
            self.nv_btn.setText(
                t("btn.night_vision_on")
                if self._night_vision
                else t("btn.night_vision")
            )
            for i, key in enumerate(self.nav_names):
                item = self.nav.item(i)
                if item is not None:
                    item.setText(t(f"nav.{key}"))
            if hasattr(self.context, "retranslate"):
                self.context.retranslate()
            if hasattr(self.help_panel, "retranslate"):
                self.help_panel.retranslate()
            if hasattr(self.prefs_panel, "retranslate"):
                self.prefs_panel.retranslate()
            for i in range(self.configurar.tabs.count()):
                w = self.configurar.tabs.widget(i)
                if w is self.prefs_panel:
                    self.configurar.tabs.setTabText(i, t("prefs.title"))
                elif w is self.help_panel:
                    self.configurar.tabs.setTabText(i, t("help.panel_title"))

        def _open_help(self) -> None:
            area = (
                self.nav_names[self.nav.currentRow()]
                if 0 <= self.nav.currentRow() < len(self.nav_names)
                else "Noite"
            )
            topic = area_to_help_topic(area)
            try:
                cfg_idx = self.nav_names.index("Configurar")
            except ValueError:
                return
            self.nav.setCurrentRow(cfg_idx)
            for i in range(self.configurar.tabs.count()):
                if self.configurar.tabs.widget(i) is self.help_panel:
                    self.configurar.tabs.setCurrentIndex(i)
                    break
            self.help_panel.select_topic(topic)

        def _fit_to_available_screen(self) -> None:
            """Ajusta a janela a availableGeometry (evita cortar barra de tarefas)."""
            app = QApplication.instance()
            screen = app.primaryScreen() if app is not None else None
            if screen is None:
                self.resize(1100, 700)
                return
            ag = screen.availableGeometry()
            margin = 32
            target_w = min(1180, ag.width() - margin)
            target_h = min(760, ag.height() - margin)
            # Em monitores baixos, usar quase toda a altura util
            if ag.height() < 800:
                target_h = max(520, ag.height() - margin)
            if ag.width() < 1280:
                target_w = max(720, ag.width() - margin)
            target_w = max(self.minimumWidth(), min(target_w, ag.width() - 8))
            target_h = max(self.minimumHeight(), min(target_h, ag.height() - 8))
            self.resize(target_w, target_h)
            frame = self.frameGeometry()
            frame.moveCenter(ag.center())
            self.move(frame.topLeft())

        def showEvent(self, event: Any) -> None:  # noqa: N802
            super().showEvent(event)
            # Re-centrar na primeira exibicao se ainda sair do ecra
            if not getattr(self, "_fitted_once", False):
                self._fitted_once = True
                self._fit_to_available_screen()

        def _on_night_vision(self, enabled: bool) -> None:
            self._apply_night_vision(bool(enabled))
            save_night_vision_pref(bool(enabled))

        def _apply_night_vision(self, enabled: bool) -> None:
            self._night_vision = enabled
            self.nv_btn.setText(
                t("btn.night_vision_on") if enabled else t("btn.night_vision")
            )
            if self._app is not None:
                apply_theme(self._app, night_vision=enabled)

        def _context_panels(self) -> list[Any]:
            return [
                self.night,
                self.program_active,
                self.import_panel,
                self.radio_panel,
                self.specialty_panel,
                self.timing_panel,
                self.session_panel,
                self.observe_panel,
                self.analyze_panel,
            ]

        def _select_tab_by_name(self, tabs_widget: Any, name: str | None) -> None:
            if not name or tabs_widget is None:
                return
            for i in range(tabs_widget.count()):
                if tabs_widget.tabText(i) == name:
                    tabs_widget.setCurrentIndex(i)
                    return

        def _navigate_to(
            self,
            area: str | None,
            *,
            hub_tab: str | None = None,
            analyze_tab: str | None = None,
            network: str | None = None,
            product_id: str | None = None,
        ) -> None:
            if not area:
                return
            try:
                idx = self.nav_names.index(area)
            except ValueError:
                return
            self.nav.setCurrentRow(idx)
            if area == "Observatorio":
                self._select_tab_by_name(self.observatorio.tabs, hub_tab)
                if hub_tab == "Importar" and "radio" in (analyze_tab or "").lower():
                    self._select_tab_by_name(self.import_hub.tabs, "Radio")
                if hub_tab == "Observar" and analyze_tab:
                    fn = getattr(self.observe_panel, "focus_tab", None)
                    if callable(fn):
                        fn(analyze_tab)
            elif area == "Noite":
                self._select_tab_by_name(self.noite_hub.tabs, hub_tab)
            elif area == "Configurar":
                self._select_tab_by_name(self.configurar.tabs, hub_tab)
            elif area == "Analisar" and analyze_tab:
                fn = getattr(self.analyze_panel, "focus_tab", None)
                if callable(fn):
                    fn(analyze_tab)
            elif area == "Contribuir":
                fn = getattr(self.contribute, "focus_network", None)
                if callable(fn):
                    fn(network, product_id=product_id)

        def _sync_shell_context(self) -> None:
            sid = self.context.site.currentData()
            pid = self.context.program.currentData()
            for panel in self._context_panels():
                fn = getattr(panel, "set_shell_context", None)
                if callable(fn):
                    fn(site_id=sid, program_id=pid)
            self._sync_shell_night_date()

        def _on_shell_site(self, site_id: object) -> None:
            for panel in self._context_panels():
                fn = getattr(panel, "set_shell_context", None)
                if callable(fn):
                    fn(site_id=site_id, program_id=self.context.program.currentData())

        def _on_shell_program(self, program_id: object) -> None:
            for panel in self._context_panels():
                fn = getattr(panel, "set_shell_context", None)
                if callable(fn):
                    fn(site_id=self.context.site.currentData(), program_id=program_id)

        def _on_shell_night_date(self, night_date: object) -> None:
            fn = getattr(self.night, "set_shell_night_date", None)
            if callable(fn):
                fn(str(night_date))

        def _sync_shell_night_date(self) -> None:
            fn = getattr(self.night, "set_shell_night_date", None)
            if callable(fn):
                fn(self.context.night_date_iso())

        def _on_entities_changed(self) -> None:
            self.night.load_sites()
            self.import_panel.load_workspace()
            self.contribute.load_workspace()
            self.session_panel.reload()
            self.equipment_page.reload()
            self.programs_page.reload()
            self.targets_page.reload()
            self.sites_page.reload()
            self.observe_panel.reload()
            self.timing_panel.reload()
            self.radio_panel.reload()
            self.specialty_panel.reload()
            self.program_active.reload()
            self._reload_context()
            self._fill_planos()
            self.archive_panel.reload()
            self.catalog_panel.reload()
            self._sync_shell_context()

        def _on_nav(self, index: int) -> None:
            self.stack.setCurrentIndex(index)
            if 0 <= index < len(self.nav_names):
                self._status.showMessage(
                    f"{self.nav_names[index]}  ·  db={self.db_path}"
                )

        def _placeholder_page(self, title: str, body: str) -> QWidget:
            w = QWidget()
            v = QVBoxLayout(w)
            v.setContentsMargins(16, 12, 16, 12)
            t = QLabel(title)
            t.setObjectName("pageTitle")
            h = QLabel(body)
            h.setObjectName("emptyState")
            h.setWordWrap(True)
            v.addWidget(t)
            v.addWidget(h)
            v.addStretch(1)
            return w

        def _table_page(self) -> QWidget:
            w = QWidget()
            v = QVBoxLayout(w)
            v.setContentsMargins(16, 12, 16, 12)
            title = QLabel()
            title.setObjectName("pageTitle")
            empty = QLabel()
            empty.setObjectName("emptyState")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.hide()
            table = QTableWidget(0, 4)
            table.setAlternatingRowColors(True)
            table.horizontalHeader().setStretchLastSection(True)
            v.addWidget(title)
            v.addWidget(empty)
            v.addWidget(table, 1)
            w._title = title  # type: ignore[attr-defined]
            w._empty = empty  # type: ignore[attr-defined]
            w._table = table  # type: ignore[attr-defined]
            return w

        def _workspace(self):
            ws = self.archive.list_workspaces()
            return ws[0] if ws else None

        def _reload_context(self) -> None:
            ws = self._workspace()
            if ws is None:
                return
            sites = self.archive.list_sites(ws.id)
            programs = self.archive.list_programs(ws.id)
            self.context.reload(sites=sites, programs=programs)

        def _fill_planos(self) -> None:
            ws = self._workspace()
            if ws is None:
                return

            def fill(
                page: QWidget,
                headers: list[str],
                rows: list[list[str]],
                title: str,
                module: str,
            ) -> None:
                page._title.setText(title)  # type: ignore[attr-defined]
                t: QTableWidget = page._table  # type: ignore[attr-defined]
                empty: QLabel = page._empty  # type: ignore[attr-defined]
                t.clear()
                t.setColumnCount(len(headers))
                t.setHorizontalHeaderLabels(headers)
                t.setRowCount(len(rows))
                for r, row in enumerate(rows):
                    for c, val in enumerate(row):
                        t.setItem(r, c, QTableWidgetItem(val))
                if rows:
                    empty.hide()
                    t.show()
                else:
                    empty.setText(empty_state_text(module))
                    empty.show()
                    t.hide()

            plans = self.archive.list_daily_plans(ws.id)
            fill(
                self.pages["Plano diario"],
                ["Noite", "Estado", "Site", "Id"],
                [
                    [p.night_date, p.state, str(p.site_id)[:8], str(p.id)[:8]]
                    for p in plans
                ],
                f"Planos ({len(plans)})",
                "Plano diario",
            )

        def refresh(self) -> None:
            self.night.load_sites()
            self.contribute.load_workspace()
            self.import_panel.load_workspace()
            self.sites_page.reload()
            self.programs_page.reload()
            self.targets_page.reload()
            self.equipment_page.reload()
            self.session_panel.reload()
            self.observe_panel.reload()
            self.timing_panel.reload()
            self.radio_panel.reload()
            self.specialty_panel.reload()
            self.archive_panel.reload()
            self.catalog_panel.reload()
            self.program_active.reload()
            self._reload_context()
            self._fill_planos()
            self._sync_shell_context()

    db = Path(db_path) if db_path else default_db_path()
    archive = SqliteArchive(db)
    archive.migrate()
    # QtWebEngine (AC-095) exige AA_ShareOpenGLContexts — so com embutido opt-in.
    _want_web = (os.environ.get("ASTROCITIZEN_WEBENGINE") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    if _want_web:
        try:
            from PySide6.QtCore import Qt as _Qt

            QApplication.setAttribute(
                _Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True
            )
        except Exception:
            pass
    app = QApplication(sys.argv)
    lang = resolve_ui_lang(load_ui_lang_pref(), detected=detect_system_lang())
    set_current_lang(lang)
    nv_pref = load_night_vision_pref()
    apply_theme(app, night_vision=nv_pref)
    win = MainWindow(archive, db)
    win.show()
    code = app.exec()
    archive.close()
    return int(code)


# Exportado para testes sem abrir display
NAV_AREA_KEYS = (
    "Noite",
    "Observatorio",
    "Catalogo",
    "Analisar",
    "Contribuir",
    "Arquivo",
    "Configurar",
)
