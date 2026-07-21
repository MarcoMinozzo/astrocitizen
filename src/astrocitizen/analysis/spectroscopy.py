"""Extracao espectro 1D (esqueleto PO-B01 / inicio AC-100)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import numpy as np
from astropy.io import fits

from astrocitizen.adapters.fs import LocalArtifactStore
from astrocitizen.reduction.models import AnalysisProduct
from astrocitizen.shared.errors import DomainError
from astrocitizen.shared.ids import new_id
from astrocitizen.shared.timeutil import utc_now_iso


def extract_trace(
    data: np.ndarray,
    *,
    trace_y: float,
    half_width: int = 3,
    axis: str = "x",
) -> np.ndarray:
    """Soma espacial ao longo do trace; dispersao em `axis` (x ou y)."""
    arr = np.asarray(data, dtype=np.float64)
    if arr.ndim != 2:
        raise DomainError("espectro 2D requerido")
    hw = max(int(half_width), 0)
    if axis == "x":
        y0 = int(round(trace_y))
        y1, y2 = max(0, y0 - hw), min(arr.shape[0], y0 + hw + 1)
        if y2 <= y1:
            raise DomainError("trace_y fora da imagem")
        return arr[y1:y2, :].sum(axis=0)
    if axis == "y":
        x0 = int(round(trace_y))
        x1, x2 = max(0, x0 - hw), min(arr.shape[1], x0 + hw + 1)
        if x2 <= x1:
            raise DomainError("trace fora da imagem")
        return arr[:, x1:x2].sum(axis=1)
    raise DomainError("axis deve ser x ou y")


def wavelength_linear(
    n_pix: int,
    *,
    wave0_nm: float | None = None,
    wave1_nm: float | None = None,
    pix_a: float | None = None,
    wave_a_nm: float | None = None,
    pix_b: float | None = None,
    wave_b_nm: float | None = None,
) -> np.ndarray:
    """Solucao linear simples (esqueleto AC-101)."""
    if n_pix < 2:
        raise DomainError("espectro demasiado curto")
    if wave0_nm is not None and wave1_nm is not None:
        return np.linspace(float(wave0_nm), float(wave1_nm), n_pix)
    if None not in (pix_a, wave_a_nm, pix_b, wave_b_nm):
        pa, pb = float(pix_a), float(pix_b)
        if abs(pb - pa) < 1e-9:
            raise DomainError("pix_a e pix_b iguais")
        cdelt = (float(wave_b_nm) - float(wave_a_nm)) / (pb - pa)
        crval = float(wave_a_nm) - pa * cdelt
        return crval + np.arange(n_pix, dtype=float) * cdelt
    # fallback: indices como nm proxy
    return np.arange(n_pix, dtype=float)


class ExtractSpectrum1D:
    """Produto spectrum_1d a partir de frame 2D (slit)."""

    def __init__(self, archive: Any, store: LocalArtifactStore) -> None:
        self.archive = archive
        self.store = store

    def execute(
        self,
        *,
        workspace_id: UUID,
        fits_uri: str,
        trace_y: float,
        half_width: int = 3,
        axis: str = "x",
        wave0_nm: float | None = None,
        wave1_nm: float | None = None,
        pix_a: float | None = None,
        wave_a_nm: float | None = None,
        pix_b: float | None = None,
        wave_b_nm: float | None = None,
        program_id: UUID | None = None,
        observation_id: UUID | None = None,
        objname: str | None = None,
    ) -> AnalysisProduct:
        path = self.store.resolve(fits_uri)
        with fits.open(path) as hdul:
            data = np.asarray(hdul[0].data, dtype=np.float64)
            hdr = hdul[0].header
        flux = extract_trace(data, trace_y=trace_y, half_width=half_width, axis=axis)
        wave = wavelength_linear(
            len(flux),
            wave0_nm=wave0_nm,
            wave1_nm=wave1_nm,
            pix_a=pix_a,
            wave_a_nm=wave_a_nm,
            pix_b=pix_b,
            wave_b_nm=wave_b_nm,
        )
        when = hdr.get("DATE-OBS") or utc_now_iso()
        name = objname or hdr.get("OBJECT") or hdr.get("OBJNAME") or "SPEC"
        out_key = f"analysis/spectrum/{new_id()}.fits"
        out_path = self.store.root / out_key
        out_path.parent.mkdir(parents=True, exist_ok=True)
        hdu = fits.PrimaryHDU(data=flux.astype(np.float32))
        hdu.header["OBJECT"] = str(name)[:68]
        hdu.header["DATE-OBS"] = when
        hdu.header["CRVAL1"] = float(wave[0])
        hdu.header["CDELT1"] = float(wave[1] - wave[0])
        hdu.header["CRPIX1"] = 1.0
        hdu.header["CTYPE1"] = "WAVE"
        hdu.header["CUNIT1"] = "nm"
        hdu.header["ORIGIN"] = "AstroCitizen/0.0.1"
        hdu.writeto(out_path, overwrite=True)
        uri = out_path.as_uri()

        # downsample points for BD (cap)
        step = max(1, len(wave) // 64)
        points = [
            {
                "t_utc": when,
                "sequence_index": i,
                "x": float(wave[i]),
                "y": float(flux[i]),
                "y_err": None,
                "band": "spec",
                "meta": {"unit_x": "nm"},
            }
            for i in range(0, len(wave), step)
        ]
        product = AnalysisProduct(
            id=new_id(),
            workspace_id=workspace_id,
            program_id=program_id,
            product_type="spectrum_1d",
            version_num=1,
            is_publishable=False,
            parameters={
                "method": "slit_sum",
                "trace_y": trace_y,
                "half_width": half_width,
                "axis": axis,
                "fits_uri": fits_uri,
                "spectrum_uri": uri,
                "n_pix": len(flux),
                "wave0_nm": float(wave[0]),
                "wave1_nm": float(wave[-1]),
                "objname": name,
            },
            summary={
                "n_points": len(points),
                "flux_mean": float(np.mean(flux)),
                "wave0_nm": float(wave[0]),
                "wave1_nm": float(wave[-1]),
            },
            state="ready",
        )
        product = self.archive.save_analysis_product(product)
        if observation_id:
            self.archive.link_product_observation(product.id, observation_id)
        self.archive.save_measurement_points(product.id, points)
        return product
