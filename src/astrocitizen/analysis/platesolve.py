"""Caso de uso PlateSolve -> produto wcs_solution (AC-110)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID

from astrocitizen.adapters.fs import LocalArtifactStore
from astrocitizen.ports.platesolve import PlateSolvePort, PlateSolveResult
from astrocitizen.reduction.models import AnalysisProduct
from astrocitizen.shared.errors import DomainError
from astrocitizen.shared.ids import new_id


class PlateSolve:
    """Executa plate-solve e persiste FITS com WCS + AnalysisProduct."""

    def __init__(
        self,
        archive: Any,
        store: LocalArtifactStore,
        solver: PlateSolvePort,
    ) -> None:
        self.archive = archive
        self.store = store
        self.solver = solver

    def execute(
        self,
        *,
        workspace_id: UUID,
        fits_uri: str,
        ra_hint_deg: float | None = None,
        dec_hint_deg: float | None = None,
        radius_deg: float | None = None,
        scale_low_arcsec: float | None = None,
        scale_high_arcsec: float | None = None,
        timeout_s: float = 120.0,
        program_id: UUID | None = None,
        observation_id: UUID | None = None,
    ) -> tuple[AnalysisProduct, PlateSolveResult]:
        src = self.store.resolve(fits_uri)
        out_dir = self.store.root / "analysis" / "wcs" / str(new_id())
        result = self.solver.solve(
            src,
            out_dir=out_dir,
            ra_hint_deg=ra_hint_deg,
            dec_hint_deg=dec_hint_deg,
            radius_deg=radius_deg,
            scale_low_arcsec=scale_low_arcsec,
            scale_high_arcsec=scale_high_arcsec,
            timeout_s=timeout_s,
        )
        if result.wcs_fits_path is None or not Path(result.wcs_fits_path).is_file():
            raise DomainError("solver nao devolveu FITS com WCS")
        wcs_uri = self.store.put(
            Path(result.wcs_fits_path),
            key=f"analysis/wcs/{Path(result.wcs_fits_path).name}",
        )
        product = AnalysisProduct(
            id=new_id(),
            workspace_id=workspace_id,
            program_id=program_id,
            product_type="wcs_solution",
            version_num=1,
            is_publishable=False,
            parameters={
                "method": "plate_solve",
                "backend": result.backend,
                "fits_uri": fits_uri,
                "wcs_uri": wcs_uri,
                "ra_hint_deg": ra_hint_deg,
                "dec_hint_deg": dec_hint_deg,
                "radius_deg": radius_deg,
            },
            summary={
                "ra_center_deg": result.ra_center_deg,
                "dec_center_deg": result.dec_center_deg,
                "scale_arcsec": result.scale_arcsec,
                "orientation_deg": result.orientation_deg,
                "backend": result.backend,
            },
            state="ready",
        )
        product = self.archive.save_analysis_product(product)
        if observation_id:
            self.archive.link_product_observation(product.id, observation_id)
        return product, result
