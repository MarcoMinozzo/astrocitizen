"""Construcao de masters e aplicacao de calibracao."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal
from uuid import UUID

import numpy as np
from astropy.io import fits

from astrocitizen.adapters.fs import LocalArtifactStore
from astrocitizen.reduction.models import AnalysisProduct, CalibrationMaster
from astrocitizen.shared.errors import DomainError, NotFoundError
from astrocitizen.shared.ids import new_id
from astrocitizen.shared.timeutil import utc_now_iso

MasterKind = Literal["bias", "dark", "flat"]


def _load_fits_data(path: Path) -> np.ndarray:
    with fits.open(path) as hdul:
        data = hdul[0].data
        if data is None:
            raise DomainError(f"FITS sem dados: {path}")
        return np.asarray(data, dtype=np.float64)


def _write_fits(path: Path, data: np.ndarray, headers: dict[str, Any] | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    hdu = fits.PrimaryHDU(np.asarray(data, dtype=np.float32))
    if headers:
        for k, v in headers.items():
            try:
                hdu.header[str(k)[:8].upper()] = v
            except (ValueError, TypeError):
                hdu.header[str(k)[:8].upper()] = str(v)
    hdu.writeto(path, overwrite=True)
    return path


class BuildMaster:
    """Median-combine de frames -> master bias/dark/flat versionado."""

    def __init__(self, archive: Any, store: LocalArtifactStore) -> None:
        self.archive = archive
        self.store = store

    def execute(
        self,
        *,
        workspace_id: UUID,
        kind: MasterKind,
        fits_paths: list[Path],
        notes: str = "",
    ) -> CalibrationMaster:
        if not fits_paths:
            raise DomainError("lista de FITS vazia")
        stack = [_load_fits_data(p) for p in fits_paths]
        shapes = {a.shape for a in stack}
        if len(shapes) != 1:
            raise DomainError("frames com shapes diferentes")
        master = np.median(np.stack(stack, axis=0), axis=0)
        if kind == "flat":
            med = float(np.median(master))
            if med <= 0:
                raise DomainError("flat com mediana invalida")
            master = master / med

        prev = self.archive.list_calibration_masters(workspace_id, kind=kind)
        version = (max((m.version_num for m in prev), default=0) + 1)

        art_id = new_id()
        rel = f"masters/{kind}_v{version}_{art_id}.fits"
        tmp = self.store.root / ".tmp" / f"{art_id}.fits"
        _write_fits(
            tmp,
            master,
            {"IMAGETYP": kind.upper(), "NCOMBINE": len(fits_paths), "VERSION": version},
        )
        uri = self.store.put(tmp, key=rel)
        tmp.unlink(missing_ok=True)
        self.archive.save_artifact(
            artifact_id=art_id,
            workspace_id=workspace_id,
            kind=f"master_{kind}",
            uri=uri,
            filename=Path(rel).name,
            size_bytes=self.store.resolve(uri).stat().st_size,
        )
        rec = CalibrationMaster(
            id=new_id(),
            workspace_id=workspace_id,
            kind=kind,
            version_num=version,
            artifact_id=art_id,
            parameters={"ncombine": len(fits_paths), "method": "median"},
            notes=notes,
            created_at=utc_now_iso(),
        )
        return self.archive.save_calibration_master(rec)


class ApplyCalibration:
    """(light - dark) / flat -> FITS reduzido + AnalysisProduct."""

    def __init__(self, archive: Any, store: LocalArtifactStore) -> None:
        self.archive = archive
        self.store = store

    def execute(
        self,
        *,
        workspace_id: UUID,
        light_uri: str,
        observation_id: UUID | None = None,
        program_id: UUID | None = None,
        dark_master_id: UUID | None = None,
        flat_master_id: UUID | None = None,
        bias_master_id: UUID | None = None,
    ) -> AnalysisProduct:
        light = _load_fits_data(self.store.resolve(light_uri))
        calibrated = light.astype(np.float64)

        def _master_data(mid: UUID | None) -> np.ndarray | None:
            if mid is None:
                return None
            m = self.archive.get_calibration_master(mid)
            if m is None or m.artifact_id is None:
                raise NotFoundError(f"master nao encontrado: {mid}")
            uri = self.archive.get_artifact_uri(m.artifact_id)
            if uri is None:
                raise NotFoundError("artefacto do master em falta")
            return _load_fits_data(self.store.resolve(uri))

        bias = _master_data(bias_master_id)
        dark = _master_data(dark_master_id)
        flat = _master_data(flat_master_id)
        if bias is not None:
            calibrated = calibrated - bias
        if dark is not None:
            calibrated = calibrated - dark
        if flat is not None:
            calibrated = calibrated / np.where(flat == 0, np.nan, flat)
            calibrated = np.nan_to_num(calibrated, nan=0.0)

        prod_id = new_id()
        art_id = new_id()
        rel = f"reduced/{prod_id}.fits"
        tmp = self.store.root / ".tmp" / f"{art_id}.fits"
        _write_fits(
            tmp,
            calibrated,
            {
                "IMAGETYP": "REDUCED",
                "BZERO": 0,
                "PRODUCT": str(prod_id),
            },
        )
        uri = self.store.put(tmp, key=rel)
        tmp.unlink(missing_ok=True)
        self.archive.save_artifact(
            artifact_id=art_id,
            workspace_id=workspace_id,
            kind="fits_reduced",
            uri=uri,
            filename=Path(rel).name,
            observation_id=observation_id,
            size_bytes=self.store.resolve(uri).stat().st_size,
        )
        product = AnalysisProduct(
            id=prod_id,
            workspace_id=workspace_id,
            program_id=program_id,
            product_type="calibrated_frame",
            version_num=1,
            is_publishable=False,
            parameters={
                "bias": str(bias_master_id) if bias_master_id else None,
                "dark": str(dark_master_id) if dark_master_id else None,
                "flat": str(flat_master_id) if flat_master_id else None,
                "artifact_id": str(art_id),
                "uri": uri,
            },
            summary={
                "mean": float(np.mean(calibrated)),
                "median": float(np.median(calibrated)),
                "std": float(np.std(calibrated)),
                "shape": list(calibrated.shape),
            },
            state="ready",
        )
        product = self.archive.save_analysis_product(product)
        if observation_id:
            self.archive.link_product_observation(product.id, observation_id)
        return product
