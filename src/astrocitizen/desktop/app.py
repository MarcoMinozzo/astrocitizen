"""Shell GUI PySide6 (AC-071...073)  navegacao por modulos."""

from __future__ import annotations

import sys
from pathlib import Path


def run_gui(db_path: str | None = None) -> int:
    try:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import (
            QApplication,
            QHBoxLayout,
            QLabel,
            QListWidget,
            QMainWindow,
            QStackedWidget,
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
    from astrocitizen.shared.paths import default_db_path

    class MainWindow(QMainWindow):
        def __init__(self, archive: SqliteArchive) -> None:
            super().__init__()
            self.archive = archive
            self.setWindowTitle("AstroCitizen")
            self.resize(1000, 640)

            root = QWidget()
            layout = QHBoxLayout(root)
            self.nav = QListWidget()
            self.nav.addItems(
                ["Sites", "Equipamento", "Programas", "Plano diario", "Sessao", "Arquivo"]
            )
            self.nav.setFixedWidth(160)
            self.stack = QStackedWidget()
            layout.addWidget(self.nav)
            layout.addWidget(self.stack, 1)
            self.setCentralWidget(root)

            self.pages = {
                "Sites": self._table_page(),
                "Equipamento": self._table_page(),
                "Programas": self._table_page(),
                "Plano diario": self._table_page(),
                "Sessao": self._table_page(),
                "Arquivo": self._table_page(),
            }
            for name in [
                "Sites",
                "Equipamento",
                "Programas",
                "Plano diario",
                "Sessao",
                "Arquivo",
            ]:
                self.stack.addWidget(self.pages[name])

            self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)
            self.nav.setCurrentRow(0)
            self.refresh()

        def _table_page(self) -> QWidget:
            w = QWidget()
            v = QVBoxLayout(w)
            title = QLabel()
            title.setAlignment(Qt.AlignmentFlag.AlignLeft)
            table = QTableWidget(0, 4)
            v.addWidget(title)
            v.addWidget(table)
            w._title = title  # type: ignore[attr-defined]
            w._table = table  # type: ignore[attr-defined]
            return w

        def refresh(self) -> None:
            workspaces = self.archive.list_workspaces()
            if not workspaces:
                return
            ws = workspaces[0]

            def fill(page: QWidget, headers: list[str], rows: list[list[str]], title: str) -> None:
                page._title.setText(title)  # type: ignore[attr-defined]
                t: QTableWidget = page._table  # type: ignore[attr-defined]
                t.clear()
                t.setColumnCount(len(headers))
                t.setHorizontalHeaderLabels(headers)
                t.setRowCount(len(rows))
                for r, row in enumerate(rows):
                    for c, val in enumerate(row):
                        t.setItem(r, c, QTableWidgetItem(val))

            sites = self.archive.list_sites(ws.id)
            fill(
                self.pages["Sites"],
                ["Nome", "Lat", "Lon", "TZ"],
                [
                    [s.name, f"{s.latitude_deg:.4f}", f"{s.longitude_deg:.4f}", s.timezone]
                    for s in sites
                ],
                f"Sites ({len(sites)})",
            )
            eqs = self.archive.list_equipment(ws.id)
            fill(
                self.pages["Equipamento"],
                ["Tipo", "Nome", "Backend", "OK"],
                [
                    [e.type, e.name, e.backend or "-", "sim" if e.available else "nao"]
                    for e in eqs
                ],
                f"Equipamento ({len(eqs)})",
            )
            progs = self.archive.list_programs(ws.id)
            fill(
                self.pages["Programas"],
                ["Template", "Estado", "Pri", "Nome"],
                [[p.template_id, p.state, str(p.priority), p.name] for p in progs],
                f"Programas ({len(progs)})",
            )
            plans = self.archive.list_daily_plans(ws.id)
            fill(
                self.pages["Plano diario"],
                ["Noite", "Estado", "Site", "Id"],
                [
                    [p.night_date, p.state, str(p.site_id)[:8], str(p.id)[:8]]
                    for p in plans
                ],
                f"Planos ({len(plans)})",
            )
            sessions = self.archive.list_sessions(ws.id)
            fill(
                self.pages["Sessao"],
                ["Estado", "Inicio", "Plano", "Id"],
                [
                    [s.state, s.started_at_utc, str(s.daily_plan_id)[:8], str(s.id)[:8]]
                    for s in sessions
                ],
                f"Sessoes ({len(sessions)})",
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
            )

    db = Path(db_path) if db_path else default_db_path()
    archive = SqliteArchive(db)
    archive.migrate()
    app = QApplication(sys.argv)
    win = MainWindow(archive)
    win.show()
    code = app.exec()
    archive.close()
    return int(code)
