"""Painel Sessao: wizard captura IN-CAP (site/programa/alvo -> FITS)."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def build_session_dashboard() -> type:
    from PySide6.QtWidgets import (
        QComboBox,
        QDoubleSpinBox,
        QFormLayout,
        QHBoxLayout,
        QLabel,
        QMessageBox,
        QPushButton,
        QSpinBox,
        QTableWidget,
        QTableWidgetItem,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    from astrocitizen.adapters.fs import LocalArtifactStore
    from astrocitizen.adapters.hardware import create_camera
    from astrocitizen.observatory import (
        CaptureObservation,
        ExecuteSession,
        prepare_wizard_session,
        reset_block_for_capture,
    )
    from astrocitizen.shared.errors import DomainError, NotFoundError
    from astrocitizen.shared.paths import default_artifacts_root

    class SessionDashboard(QWidget):
        def __init__(
            self,
            archive: Any,
            *,
            artifacts_root: Path | None = None,
            on_changed: Any | None = None,
        ) -> None:
            super().__init__()
            self.archive = archive
            self.artifacts_root = Path(artifacts_root or default_artifacts_root())
            self.on_changed = on_changed
            self._ctx = None  # WizardSessionContext | None
            self._camera = None

            lay = QVBoxLayout(self)
            lay.setContentsMargins(16, 12, 16, 12)
            title = QLabel("Sessao — captura (IN-CAP)")
            title.setObjectName("pageTitle")
            lay.addWidget(title)

            form = QFormLayout()
            self.site_combo = QComboBox()
            self.program_combo = QComboBox()
            self.target_combo = QComboBox()
            self.backend = QComboBox()
            self.backend.addItem("sim (simulador)", "sim")
            self.backend.addItem("alpaca", "alpaca")
            self.backend.addItem("udrv (SBIG)", "udrv")
            self.exptime = QDoubleSpinBox()
            self.exptime.setRange(0.1, 3600.0)
            self.exptime.setDecimals(1)
            self.exptime.setValue(1.0)
            self.n_frames = QSpinBox()
            self.n_frames.setRange(1, 50)
            self.n_frames.setValue(1)
            form.addRow("Site", self.site_combo)
            form.addRow("Programa", self.program_combo)
            form.addRow("Alvo", self.target_combo)
            form.addRow("Backend", self.backend)
            form.addRow("Exposicao (s)", self.exptime)
            form.addRow("Frames", self.n_frames)
            lay.addLayout(form)

            bar = QHBoxLayout()
            self.btn_start = QPushButton("Iniciar sessao")
            self.btn_capture = QPushButton("Capturar")
            self.btn_end = QPushButton("Terminar sessao")
            self.btn_refresh = QPushButton("Atualizar listas")
            self.btn_refresh.setObjectName("secondaryBtn")
            bar.addWidget(self.btn_start)
            bar.addWidget(self.btn_capture)
            bar.addWidget(self.btn_end)
            bar.addWidget(self.btn_refresh)
            bar.addStretch(1)
            lay.addLayout(bar)

            self.status = QLabel("Sem sessao activa.")
            self.status.setObjectName("emptyState")
            lay.addWidget(self.status)

            self.log = QTextEdit()
            self.log.setReadOnly(True)
            self.log.setMaximumHeight(120)
            lay.addWidget(self.log)

            self.table = QTableWidget(0, 4)
            self.table.setAlternatingRowColors(True)
            self.table.setHorizontalHeaderLabels(
                ["Estado", "Inicio", "Plano", "Id"]
            )
            self.table.horizontalHeader().setStretchLastSection(True)
            lay.addWidget(self.table, 1)

            self.btn_start.clicked.connect(self._start)
            self.btn_capture.clicked.connect(self._capture)
            self.btn_end.clicked.connect(self._end)
            self.btn_refresh.clicked.connect(self.reload)

        def _append(self, msg: str) -> None:
            self.log.append(msg)

        def reload(self) -> None:
            ws = self.archive.list_workspaces()
            if not ws:
                return
            wid = ws[0].id
            sites = self.archive.list_sites(wid)
            progs = self.archive.list_programs(wid)
            targets = self.archive.list_targets(wid)

            def refill(combo: QComboBox, items: list, label_fn) -> None:
                cur = combo.currentData()
                combo.clear()
                for it in items:
                    combo.addItem(label_fn(it), it.id)
                if cur is not None:
                    i = combo.findData(cur)
                    if i >= 0:
                        combo.setCurrentIndex(i)

            refill(
                self.site_combo,
                sites,
                lambda s: f"{s.name} ({s.latitude_deg:.2f},{s.longitude_deg:.2f})",
            )
            refill(
                self.program_combo,
                progs,
                lambda p: f"{p.template_id} · {p.name} [{p.state}]",
            )
            refill(
                self.target_combo,
                targets,
                lambda t: f"{t.designation}"
                + (f" RA={t.ra_deg:.3f}" if t.ra_deg is not None else ""),
            )

            sessions = self.archive.list_sessions(wid)
            self.table.setRowCount(len(sessions))
            for r, s in enumerate(sessions):
                vals = [
                    s.state,
                    s.started_at_utc,
                    str(s.daily_plan_id)[:8],
                    str(s.id)[:8],
                ]
                for c, v in enumerate(vals):
                    self.table.setItem(r, c, QTableWidgetItem(v))

            if self._ctx and self._ctx.session.state == "active":
                self.status.setText(
                    f"Sessao activa {str(self._ctx.session.id)[:8]} · "
                    f"noite {self._ctx.plan.night_date} · "
                    f"bloco {str(self._ctx.block.id)[:8]}"
                )
            elif not sessions:
                self.status.setText("Sem sessao. Escolha site/programa/alvo e Iniciar.")

        def _start(self) -> None:
            ws = self.archive.list_workspaces()
            if not ws:
                QMessageBox.warning(self, "Sessao", "Sem workspace.")
                return
            site_id = self.site_combo.currentData()
            prog_id = self.program_combo.currentData()
            tgt_id = self.target_combo.currentData()
            if not site_id or not prog_id or not tgt_id:
                QMessageBox.warning(
                    self, "Sessao", "Cadastre e selecione site, programa e alvo."
                )
                return
            try:
                ctx = prepare_wizard_session(
                    self.archive,
                    workspace_id=ws[0].id,
                    site_id=site_id,
                    program_id=prog_id,
                    target_id=tgt_id,
                )
            except (DomainError, NotFoundError) as exc:
                QMessageBox.critical(self, "Sessao", str(exc))
                return
            self._ctx = ctx
            verb = "Criada" if ctx.created_session else "Reutilizada"
            self._append(
                f"{verb} sessao {ctx.session.id} · plano {ctx.plan.night_date} · "
                f"bloco {ctx.block.id}"
            )
            self.reload()
            if self.on_changed:
                self.on_changed()

        def _capture(self) -> None:
            if self._ctx is None or self._ctx.session.state != "active":
                # try resume from last active
                ws = self.archive.list_workspaces()
                if not ws:
                    return
                actives = self.archive.list_sessions(ws[0].id, state="active")
                if not actives:
                    QMessageBox.information(
                        self, "Sessao", "Inicie uma sessao primeiro."
                    )
                    return
                QMessageBox.information(
                    self,
                    "Sessao",
                    "Inicie pelo botao Iniciar (liga programa/alvo ao bloco).",
                )
                return

            backend = self.backend.currentData() or "sim"
            n = int(self.n_frames.value())
            exptime = float(self.exptime.value())
            store = LocalArtifactStore(self.artifacts_root)
            try:
                cam = create_camera(str(backend))
                cam.connect()
            except DomainError as exc:
                QMessageBox.critical(self, "Camera", str(exc))
                return
            self._camera = cam
            capture = CaptureObservation(self.archive, cam, store)
            ok = 0
            for i in range(n):
                try:
                    reset_block_for_capture(self.archive, self._ctx.block.id)
                    obs = capture.execute(
                        session_id=self._ctx.session.id,
                        block_id=self._ctx.block.id,
                        exptime_s=exptime,
                        frame_type="light",
                    )
                    night = self._ctx.plan.night_date
                    fits_path = store.root / "raw" / night / f"{obs.id}.fits"
                    self._append(
                        f"[{i+1}/{n}] obs={obs.id}  "
                        f"sim={obs.simulated}  fits={fits_path}"
                    )
                    ok += 1
                except (DomainError, NotFoundError) as exc:
                    self._append(f"Erro frame {i+1}: {exc}")
                    QMessageBox.warning(self, "Captura", str(exc))
                    break
            self.status.setText(f"Capturados {ok}/{n} frames.")
            self.reload()
            if self.on_changed:
                self.on_changed()

        def _end(self) -> None:
            sid = None
            if self._ctx is not None:
                sid = self._ctx.session.id
            else:
                ws = self.archive.list_workspaces()
                if ws:
                    act = self.archive.list_sessions(ws[0].id, state="active")
                    if act:
                        sid = act[0].id
            if sid is None:
                QMessageBox.information(self, "Sessao", "Nenhuma sessao activa.")
                return
            try:
                ended = ExecuteSession(self.archive).end(sid)
            except (DomainError, NotFoundError) as exc:
                QMessageBox.critical(self, "Sessao", str(exc))
                return
            self._append(f"Sessao terminada {ended.id} estado={ended.state}")
            self._ctx = None
            if self._camera is not None:
                try:
                    self._camera.disconnect()
                except Exception:
                    pass
                self._camera = None
            self.reload()
            if self.on_changed:
                self.on_changed()

    return SessionDashboard
