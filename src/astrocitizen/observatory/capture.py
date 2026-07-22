"""Registo de Observacao + FITS (RN-060...062, AC-051/052)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID

from astrocitizen.adapters.fs import LocalArtifactStore
from astrocitizen.observatory.failure import mark_block_failed
from astrocitizen.observatory.models import ObservationRecord
from astrocitizen.shared.errors import DomainError, NotFoundError
from astrocitizen.shared.ids import new_id
from astrocitizen.shared.timeutil import utc_now_iso


def build_fits_headers(
    *,
    site: Any,
    session: Any,
    block: Any | None,
    program: Any | None,
    target: Any | None,
    camera_backend: str,
    exptime_s: float,
    frame_type: str,
    simulated: bool,
) -> dict[str, Any]:
    """Headers FITS ricos para reconstruir a noite (RN-062)."""
    headers: dict[str, Any] = {
        "ORIGIN": "AstroCitizen",
        "OBSERVAT": site.name if site else "",
        "SITELAT": site.latitude_deg if site else None,
        "SITELONG": site.longitude_deg if site else None,
        "SITEALT": site.elevation_m if site else None,
        "EXPTIME": float(exptime_s),
        "IMAGETYP": frame_type.upper(),
        "CAMBACK": camera_backend,
        "SIMULAT": simulated,
        "DATE-OBS": utc_now_iso(),
    }
    if session:
        headers["SESSION"] = str(session.id)
        headers["NIGHT"] = session.plan_snapshot.get("plan", {}).get("night_date", "")
    if block:
        headers["BLOCKID"] = str(block.id)
        headers["BLKSTAT"] = block.status
    if program:
        headers["PROGRAM"] = program.name
        headers["POTEMPL"] = program.template_id
    if target:
        headers["OBJECT"] = target.designation
        if target.ra_deg is not None:
            headers["OBJCTRA"] = target.ra_deg
        if target.dec_deg is not None:
            headers["OBJCTDEC"] = target.dec_deg
    # strip Nones
    return {k: v for k, v in headers.items() if v is not None}


class CaptureObservation:
    """Expoe com CameraPort, grava FITS imutavel e regista no Archive."""

    def __init__(
        self,
        archive: Any,
        camera: Any,
        artifact_store: LocalArtifactStore,
    ) -> None:
        self.archive = archive
        self.camera = camera
        self.artifact_store = artifact_store

    def execute(
        self,
        *,
        session_id: UUID,
        block_id: UUID | None = None,
        program_id: UUID | None = None,
        target_id: UUID | None = None,
        exptime_s: float = 1.0,
        frame_type: str = "light",
        binning: int = 1,
    ) -> ObservationRecord:
        session = self.archive.get_session(session_id)
        if session is None or session.state != "active":
            raise NotFoundError("sessao activa nao encontrada")

        block = self.archive.get_observation_block(block_id) if block_id else None
        site = self.archive.get_site(session.site_id)
        program = None
        target = None
        if block and block.program_id:
            program = self.archive.get_program(block.program_id)
        elif program_id:
            program = self.archive.get_program(program_id)
        if block and block.target_id:
            target = self.archive.get_target(block.target_id)
        elif target_id:
            target = self.archive.get_target(target_id)

        if block and target and target.ra_deg is not None and hasattr(self, "_mount"):
            pass  # mount slew handled by caller / session runner

        if block:
            block.status = "em_execucao"
            self.archive.update_observation_block(block)
            self.archive.add_session_event(
                event_id=new_id(),
                session_id=session_id,
                event_type="block.started",
                occurred_at_utc=utc_now_iso(),
                block_id=block.id,
            )

        try:
            if not self.camera.is_connected():
                self.camera.connect()
            meta = self.camera.expose(
                exptime_s=exptime_s, frame_type=frame_type, binning=binning
            )
        except DomainError as exc:
            if block:
                mark_block_failed(
                    self.archive,
                    session_id=session_id,
                    block_id=block.id,
                    reason=str(exc),
                )
            raise

        simulated = getattr(self.camera, "backend_name", "") == "sim"
        headers = build_fits_headers(
            site=site,
            session=session,
            block=block,
            program=program,
            target=target,
            camera_backend=getattr(self.camera, "backend_name", "unknown"),
            exptime_s=exptime_s,
            frame_type=frame_type,
            simulated=simulated,
        )
        headers.update({k: v for k, v in meta.items() if k not in headers})

        obs_id = new_id()
        night = session.plan_snapshot.get("plan", {}).get("night_date", "unknown")
        rel_key = f"raw/{night}/{obs_id}.fits"
        tmp = self.artifact_store.root / ".tmp" / f"{obs_id}.fits"
        tmp.parent.mkdir(parents=True, exist_ok=True)
        self.camera.save_fits(tmp, headers=headers)
        uri = self.artifact_store.put(tmp, key=rel_key)
        tmp.unlink(missing_ok=True)

        resolved_program_id = (
            block.program_id if block and block.program_id else program_id
        )
        resolved_target_id = (
            block.target_id if block and block.target_id else target_id
        )
        obs = ObservationRecord(
            id=obs_id,
            workspace_id=session.workspace_id,
            observed_at_utc=utc_now_iso(),
            site_id=session.site_id,
            session_id=session.id,
            block_id=block.id if block else None,
            program_id=resolved_program_id,
            target_id=resolved_target_id,
            instrument_config_id=block.instrument_config_id if block else None,
            camera_backend=getattr(self.camera, "backend_name", None),
            simulated=simulated,
            headers_summary={
                k: headers[k]
                for k in ("EXPTIME", "IMAGETYP", "OBJECT", "PROGRAM", "POTEMPL", "CAMBACK")
                if k in headers
            },
        )
        self.archive.save_observation(obs)
        self.archive.save_artifact(
            artifact_id=new_id(),
            workspace_id=session.workspace_id,
            kind="fits_raw",
            uri=uri,
            filename=Path(rel_key).name,
            observation_id=obs.id,
            size_bytes=self.artifact_store.resolve(uri).stat().st_size,
        )

        if block:
            block.status = "concluido"
            self.archive.update_observation_block(block)
            self.archive.add_session_event(
                event_id=new_id(),
                session_id=session_id,
                event_type="block.completed",
                occurred_at_utc=utc_now_iso(),
                block_id=block.id,
                payload={"observation_id": str(obs.id)},
            )
        return obs
