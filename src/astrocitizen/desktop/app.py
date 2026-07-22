"""Shell GUI PySide6 - navegacao + tema + Noite + Contribute + Import + CRUD."""

from __future__ import annotations

import sys
from pathlib import Path


def run_gui(db_path: str | None = None) -> int:
    try:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import (
            QApplication,
            QFrame,
            QHBoxLayout,
            QLabel,
            QListWidget,
            QListWidgetItem,
            QMainWindow,
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
    from astrocitizen.desktop.contribute import build_contribute_dashboard
    from astrocitizen.desktop.entities import (
        build_programs_page,
        build_sites_page,
        build_targets_page,
    )
    from astrocitizen.desktop.equipment import build_equipment_page
    from astrocitizen.desktop.import_panel import build_import_dashboard
    from astrocitizen.desktop.night import build_night_dashboard
    from astrocitizen.desktop.session_panel import build_session_dashboard
    from astrocitizen.desktop.theme import apply_theme, empty_state_text
    from astrocitizen.shared.paths import default_artifacts_root, default_db_path

    NightDashboard = build_night_dashboard()
    ContributeDashboard = build_contribute_dashboard()
    ImportDashboard = build_import_dashboard()
    SitesPage = build_sites_page()
    ProgramsPage = build_programs_page()
    TargetsPage = build_targets_page()
    EquipmentPage = build_equipment_page()
    SessionDashboard = build_session_dashboard()

    NAV_ITEMS: list[tuple[str, str]] = [
        ("Noite", "Noite"),
        ("Contribute", "Contribute"),
        ("Import", "Import"),
        ("Sites", "Sites"),
        ("Equipamento", "Equipamento"),
        ("Programas", "Programas"),
        ("Alvos", "Alvos"),
        ("Plano diario", "Plano diario"),
        ("Sessao", "Sessao"),
        ("Arquivo", "Arquivo"),
    ]

    class MainWindow(QMainWindow):
        def __init__(self, archive: SqliteArchive, db: Path) -> None:
            super().__init__()
            self.archive = archive
            self.db_path = db
            self.setWindowTitle("AstroCitizen")
            self.resize(1180, 760)

            outer = QWidget()
            outer_l = QVBoxLayout(outer)
            outer_l.setContentsMargins(0, 0, 0, 0)
            outer_l.setSpacing(0)

            brand = QFrame()
            brand.setObjectName("brandBar")
            brand.setStyleSheet(
                "QFrame#brandBar { background:#0e1626; border-bottom:1px solid #243049; }"
            )
            brand_l = QVBoxLayout(brand)
            brand_l.setContentsMargins(16, 10, 16, 10)
            title = QLabel("AstroCitizen")
            title.setObjectName("brandTitle")
            sub = QLabel("observatorio cidadao · desktop")
            sub.setObjectName("brandSubtitle")
            brand_l.addWidget(title)
            brand_l.addWidget(sub)
            outer_l.addWidget(brand)

            body = QWidget()
            layout = QHBoxLayout(body)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)

            self.nav = QListWidget()
            self.nav.setObjectName("navList")
            self.nav.setFixedWidth(188)
            self.nav_names = [key for key, _ in NAV_ITEMS]
            for _, label in NAV_ITEMS:
                QListWidgetItem(label, self.nav)

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
            self.night = NightDashboard(archive, artifacts_root=arts)
            self.contribute = ContributeDashboard(archive, artifacts_root=arts)
            self.import_panel = ImportDashboard(archive, artifacts_root=arts)
            self.sites_page = SitesPage(archive, on_changed=self._on_entities_changed)
            self.programs_page = ProgramsPage(archive, on_changed=self._on_entities_changed)
            self.targets_page = TargetsPage(archive, on_changed=self._on_entities_changed)
            self.equipment_page = EquipmentPage(
                archive, on_changed=self._on_entities_changed
            )
            self.session_panel = SessionDashboard(
                archive, artifacts_root=arts, on_changed=self._on_entities_changed
            )
            self.stack.addWidget(self.night)
            self.stack.addWidget(self.contribute)
            self.stack.addWidget(self.import_panel)
            self.stack.addWidget(self.sites_page)
            self.stack.addWidget(self.equipment_page)

            self.pages: dict[str, QWidget] = {}

            self.stack.addWidget(self.programs_page)
            self.stack.addWidget(self.targets_page)

            plan_page = self._table_page()
            self.pages["Plano diario"] = plan_page
            self.stack.addWidget(plan_page)

            self.stack.addWidget(self.session_panel)

            arquivo_page = self._table_page()
            self.pages["Arquivo"] = arquivo_page
            self.stack.addWidget(arquivo_page)

            self.nav.currentRowChanged.connect(self._on_nav)
            self.nav.setCurrentRow(0)
            self.refresh()

        def _on_entities_changed(self) -> None:
            self.night.load_sites()
            self.import_panel.load_workspace()
            self.contribute.load_workspace()
            self.session_panel.reload()
            self.equipment_page.reload()
            self.programs_page.reload()

        def _on_nav(self, index: int) -> None:
            self.stack.setCurrentIndex(index)
            if 0 <= index < len(self.nav_names):
                self._status.showMessage(
                    f"{self.nav_names[index]}  ·  db={self.db_path}"
                )

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

        def refresh(self) -> None:
            self.night.load_sites()
            self.contribute.load_workspace()
            self.import_panel.load_workspace()
            self.sites_page.reload()
            self.programs_page.reload()
            self.targets_page.reload()
            self.equipment_page.reload()
            self.session_panel.reload()
            workspaces = self.archive.list_workspaces()
            if not workspaces:
                return
            ws = workspaces[0]

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
            obs = self.archive.list_observations(ws.id, include_simulated=True)
            fill(
                self.pages["Arquivo"],
                ["Quando", "Sim", "Backend", "Id"],
                [
                    [
                        o.get("observed_at_utc", ""),
                        str(bool(o.get("simulated"))),
                        str(o.get("camera_backend") or "-"),
                        str(o.get("id", ""))[:8],
                    ]
                    for o in obs[:100]
                ],
                f"Observacoes ({len(obs)})",
                "Arquivo",
            )

    db = Path(db_path) if db_path else default_db_path()
    archive = SqliteArchive(db)
    archive.migrate()
    app = QApplication(sys.argv)
    apply_theme(app)
    win = MainWindow(archive, db)
    win.show()
    code = app.exec()
    archive.close()
    return int(code)
