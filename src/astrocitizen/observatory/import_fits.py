"""Importacao de FITS externos (canal IN-IMP / AC-054 inicio)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID

from astropy.io import fits

from astrocitizen.adapters.fs import LocalArtifactStore
from astrocitizen.observatory.models import ObservationRecord
from astrocitizen.shared.errors import DomainError, NotFoundError
from astrocitizen.shared.ids import new_id
from astrocitizen.shared.timeutil import utc_now_iso

FITS_SUFFIXES = {".fits", ".fit", ".fts"}


def discover_fits_paths(path: Path, *, recursive: bool = False) -> list[Path]:
    """Lista ficheiros FITS a partir de ficheiro ou directorio."""
    path = Path(path).expanduser().resolve()
    if path.is_file():
        if path.suffix.lower() not in FITS_SUFFIXES:
            raise DomainError(f"nao e FITS: {path}")
        return [path]
    if not path.is_dir():
        raise NotFoundError(f"caminho nao encontrado: {path}")
    pattern = "**/*" if recursive else "*"
    found: list[Path] = []
    for p in sorted(path.glob(pattern)):
        if p.is_file() and p.suffix.lower() in FITS_SUFFIXES:
            found.append(p)
    if not found:
        raise DomainError(f"nenhum FITS em {path}")
    return found


def _header_summary(hdr: fits.Header) -> dict[str, Any]:
    keys = (
        "OBJECT",
        "OBJNAME",
        "EXPTIME",
        "IMAGETYP",
        "FILTER",
        "DATE-OBS",
        "TELESCOP",
        "INSTRUME",
        "OBSERVER",
        "NAXIS1",
        "NAXIS2",
    )
    out: dict[str, Any] = {}
    for k in keys:
        if k in hdr:
            val = hdr[k]
            if hasattr(val, "item"):
                val = val.item()
            out[k] = val
    out["IMPORTED"] = True
    return out


def _observed_at(hdr: fits.Header) -> str:
    for key in ("DATE-OBS", "DATE", "TIME-OBS"):
        if key in hdr and hdr[key]:
            return str(hdr[key]).replace("/", "-")
    return utc_now_iso()


class ImportFits:
    """Copia FITS para ArtifactStore e cria Observation (sem sessao obrigatoria)."""

    def __init__(self, archive: Any, store: LocalArtifactStore) -> None:
        self.archive = archive
        self.store = store

    def execute(
        self,
        *,
        workspace_id: UUID,
        paths: list[Path],
        site_id: UUID | None = None,
        program_id: UUID | None = None,
        target_id: UUID | None = None,
        session_id: UUID | None = None,
        frame_type: str | None = None,
        simulated: bool = False,
        notes: str = "",
    ) -> list[ObservationRecord]:
        if not paths:
            raise DomainError("lista de FITS vazia")
        if site_id is not None and self.archive.get_site(site_id) is None:
            raise NotFoundError(f"site nao encontrado: {site_id}")
        if program_id is not None and self.archive.get_program(program_id) is None:
            raise NotFoundError(f"programa nao encontrado: {program_id}")
        if target_id is not None and self.archive.get_target(target_id) is None:
            raise NotFoundError(f"alvo nao encontrado: {target_id}")

        results: list[ObservationRecord] = []
        day = utc_now_iso()[:10]
        for src in paths:
            src = Path(src).expanduser().resolve()
            if not src.is_file():
                raise NotFoundError(f"FITS nao encontrado: {src}")
            with fits.open(src) as hdul:
                hdr = hdul[0].header
                summary = _header_summary(hdr)
                when = _observed_at(hdr)
            if frame_type:
                summary["IMAGETYP"] = frame_type.upper()

            obs_id = new_id()
            key = f"imported/{day}/{obs_id}_{src.name}"
            uri = self.store.put(src, key=key)
            size = self.store.resolve(uri).stat().st_size
            obs = ObservationRecord(
                id=obs_id,
                workspace_id=workspace_id,
                observed_at_utc=when,
                site_id=site_id,
                session_id=session_id,
                program_id=program_id,
                target_id=target_id,
                state="imported",
                camera_backend="import",
                simulated=simulated,
                headers_summary=summary,
                notes=notes or f"imported from {src.name}",
            )
            self.archive.save_observation(obs)
            self.archive.save_artifact(
                artifact_id=new_id(),
                workspace_id=workspace_id,
                kind="fits_imported",
                uri=uri,
                filename=src.name,
                observation_id=obs.id,
                size_bytes=size,
            )
            results.append(obs)
        return results
