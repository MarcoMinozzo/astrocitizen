"""Extracao espectro 1D a partir de FITS 2D (AC-100 / PO-B01).

Metodo: soma espacial ao longo do trace (+ sky opcional).
Calibracao lambda linear continua esqueleto (AC-101).
"""

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

METHOD_ID = "slit_sum_v1"


def spatial_profile(data: np.ndarray, *, axis: str = "x") -> np.ndarray:
    """Perfil espacial (mediana ao longo da dispersao)."""
    arr = np.asarray(data, dtype=np.float64)
    if arr.ndim != 2:
        raise DomainError("espectro 2D requerido")
    if axis == "x":
        # dispersao em x → perfil ao longo de y
        return np.nanmedian(arr, axis=1)
    if axis == "y":
        return np.nanmedian(arr, axis=0)
    raise DomainError("axis deve ser x ou y")


def find_trace_peak(
    data: np.ndarray,
    *,
    axis: str = "x",
    search_lo: float | None = None,
    search_hi: float | None = None,
) -> float:
    """Localiza o pico do trace no eixo espacial (centroide ponderado perto do max)."""
    profile = spatial_profile(data, axis=axis)
    n = len(profile)
    i0 = 0 if search_lo is None else max(0, int(search_lo))
    i1 = n if search_hi is None else min(n, int(search_hi) + 1)
    if i1 <= i0:
        raise DomainError("janela de procura do trace vazia")
    window = profile[i0:i1]
    if not np.isfinite(window).any():
        raise DomainError("perfil espacial sem dados finitos")
    peak_local = int(np.nanargmax(window))
    peak = i0 + peak_local
    # centroide local ±2 pix
    lo, hi = max(i0, peak - 2), min(i1, peak + 3)
    seg = profile[lo:hi]
    w = np.clip(seg - np.nanmin(seg), 0, None)
    if float(np.nansum(w)) <= 0:
        return float(peak)
    xs = np.arange(lo, hi, dtype=float)
    return float(np.nansum(xs * w) / np.nansum(w))


def _sky_bands(
    center: int,
    *,
    half_width: int,
    sky_offset: int,
    sky_half_width: int,
    n_spatial: int,
) -> list[tuple[int, int]]:
    bands: list[tuple[int, int]] = []
    for sign in (-1, 1):
        c = center + sign * int(sky_offset)
        a = max(0, c - int(sky_half_width))
        b = min(n_spatial, c + int(sky_half_width) + 1)
        # avoid overlap with object aperture
        obj_a = max(0, center - half_width)
        obj_b = min(n_spatial, center + half_width + 1)
        if b <= obj_a or a >= obj_b:
            if b > a:
                bands.append((a, b))
    return bands


def extract_trace(
    data: np.ndarray,
    *,
    trace_y: float,
    half_width: int = 3,
    axis: str = "x",
    subtract_sky: bool = False,
    sky_offset: int | None = None,
    sky_half_width: int | None = None,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Soma espacial ao longo do trace; dispersao em `axis` (x ou y).

    Se `subtract_sky`, estima ceu em bandas paralelas e subtrai por coluna/linha.
    """
    arr = np.asarray(data, dtype=np.float64)
    if arr.ndim != 2:
        raise DomainError("espectro 2D requerido")
    hw = max(int(half_width), 0)
    meta: dict[str, Any] = {
        "trace_y": float(trace_y),
        "half_width": hw,
        "axis": axis,
        "subtract_sky": bool(subtract_sky),
    }

    if axis == "x":
        y0 = int(round(trace_y))
        y1, y2 = max(0, y0 - hw), min(arr.shape[0], y0 + hw + 1)
        if y2 <= y1:
            raise DomainError("trace_y fora da imagem")
        obj = arr[y1:y2, :]
        flux = obj.sum(axis=0)
        n_ap = y2 - y1
        sky_mean = 0.0
        if subtract_sky:
            soff = int(sky_offset if sky_offset is not None else hw + 5)
            shw = int(sky_half_width if sky_half_width is not None else max(hw, 2))
            bands = _sky_bands(
                y0, half_width=hw, sky_offset=soff, sky_half_width=shw, n_spatial=arr.shape[0]
            )
            meta["sky_offset"] = soff
            meta["sky_half_width"] = shw
            meta["sky_bands"] = bands
            if bands:
                sky_stack = np.concatenate([arr[a:b, :] for a, b in bands], axis=0)
                sky_per_pix = np.nanmedian(sky_stack, axis=0)
                sky_mean = float(np.nanmedian(sky_per_pix))
                flux = flux - sky_per_pix * n_ap
            else:
                meta["sky_warning"] = "bandas de ceu vazias ou sobrepostas"
        meta["aperture"] = (y1, y2)
        meta["sky_level"] = sky_mean
        meta["n_aperture_rows"] = n_ap
        return flux, meta

    if axis == "y":
        x0 = int(round(trace_y))
        x1, x2 = max(0, x0 - hw), min(arr.shape[1], x0 + hw + 1)
        if x2 <= x1:
            raise DomainError("trace fora da imagem")
        obj = arr[:, x1:x2]
        flux = obj.sum(axis=1)
        n_ap = x2 - x1
        sky_mean = 0.0
        if subtract_sky:
            soff = int(sky_offset if sky_offset is not None else hw + 5)
            shw = int(sky_half_width if sky_half_width is not None else max(hw, 2))
            bands = _sky_bands(
                x0, half_width=hw, sky_offset=soff, sky_half_width=shw, n_spatial=arr.shape[1]
            )
            meta["sky_offset"] = soff
            meta["sky_half_width"] = shw
            meta["sky_bands"] = bands
            if bands:
                sky_stack = np.concatenate([arr[:, a:b] for a, b in bands], axis=1)
                sky_per_pix = np.nanmedian(sky_stack, axis=1)
                sky_mean = float(np.nanmedian(sky_per_pix))
                flux = flux - sky_per_pix * n_ap
            else:
                meta["sky_warning"] = "bandas de ceu vazias ou sobrepostas"
        meta["aperture"] = (x1, x2)
        meta["sky_level"] = sky_mean
        meta["n_aperture_rows"] = n_ap
        return flux, meta

    raise DomainError("axis deve ser x ou y")


def estimate_extraction_snr(flux: np.ndarray) -> float | None:
    """SNR grosseiro: (pico - mediano) / ruido robusto."""
    arr = np.asarray(flux, dtype=np.float64)
    if arr.size < 8 or not np.isfinite(arr).any():
        return None
    med = float(np.nanmedian(arr))
    mad = float(np.nanmedian(np.abs(arr - med)))
    noise = mad * 1.4826
    if noise <= 1e-12:
        q75, q25 = np.nanpercentile(arr, [75, 25])
        noise = float(q75 - q25) / 1.349
    if noise <= 1e-12:
        noise = max(abs(med) * 1e-3, 1e-6)
    peak = float(np.nanmax(arr) - med)
    if peak <= 0:
        return None
    return peak / noise


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
    """Produto spectrum_1d a partir de frame 2D (slit) — AC-100."""

    def __init__(self, archive: Any, store: LocalArtifactStore) -> None:
        self.archive = archive
        self.store = store

    def execute(
        self,
        *,
        workspace_id: UUID,
        fits_uri: str,
        trace_y: float | None = None,
        half_width: int = 3,
        axis: str = "x",
        auto_trace: bool = False,
        subtract_sky: bool = True,
        sky_offset: int | None = None,
        sky_half_width: int | None = None,
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
        if data.ndim != 2:
            raise DomainError("FITS de entrada deve ser imagem 2D (slit)")

        used_auto = bool(auto_trace or trace_y is None)
        if used_auto:
            trace_pos = find_trace_peak(data, axis=axis)
        else:
            assert trace_y is not None
            trace_pos = float(trace_y)

        flux, ext_meta = extract_trace(
            data,
            trace_y=trace_pos,
            half_width=half_width,
            axis=axis,
            subtract_sky=subtract_sky,
            sky_offset=sky_offset,
            sky_half_width=sky_half_width,
        )
        wave = wavelength_linear(
            len(flux),
            wave0_nm=wave0_nm,
            wave1_nm=wave1_nm,
            pix_a=pix_a,
            wave_a_nm=wave_a_nm,
            pix_b=pix_b,
            wave_b_nm=wave_b_nm,
        )
        snr = estimate_extraction_snr(flux)
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
        hdu.header["ACMETHOD"] = METHOD_ID
        hdu.header["TRACE_Y"] = float(trace_pos)
        hdu.header["HALFWID"] = int(half_width)
        hdu.header["AXISDIS"] = str(axis)
        hdu.header["SKYSUB"] = bool(subtract_sky)
        if snr is not None:
            hdu.header["AC_SNR"] = float(snr)
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
        calibrated = wave0_nm is not None or None not in (
            pix_a,
            wave_a_nm,
            pix_b,
            wave_b_nm,
        )
        product = AnalysisProduct(
            id=new_id(),
            workspace_id=workspace_id,
            program_id=program_id,
            product_type="spectrum_1d",
            version_num=1,
            is_publishable=False,
            parameters={
                "method": METHOD_ID,
                "trace_y": float(trace_pos),
                "half_width": half_width,
                "axis": axis,
                "auto_trace": used_auto,
                "subtract_sky": bool(subtract_sky),
                "sky_offset": ext_meta.get("sky_offset"),
                "sky_half_width": ext_meta.get("sky_half_width"),
                "fits_uri": fits_uri,
                "spectrum_uri": uri,
                "n_pix": len(flux),
                "wave0_nm": float(wave[0]),
                "wave1_nm": float(wave[-1]),
                "wavelength_calibrated": calibrated,
                "objname": name,
                "extraction": {
                    k: v
                    for k, v in ext_meta.items()
                    if k != "sky_bands"
                },
            },
            summary={
                "n_points": len(points),
                "flux_mean": float(np.nanmean(flux)),
                "flux_max": float(np.nanmax(flux)),
                "wave0_nm": float(wave[0]),
                "wave1_nm": float(wave[-1]),
                "trace_y": float(trace_pos),
                "snr_est": snr,
                "sky_level": ext_meta.get("sky_level"),
                "auto_trace": used_auto,
                "subtract_sky": bool(subtract_sky),
            },
            state="ready",
        )
        product = self.archive.save_analysis_product(product)
        if observation_id:
            self.archive.link_product_observation(product.id, observation_id)
        self.archive.save_measurement_points(product.id, points)
        return product
