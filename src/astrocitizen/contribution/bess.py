"""Export BeSS FITS 1D (PO-B02/B03) - keywords BSS_*."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from astropy.io import fits

from astrocitizen.shared.errors import DomainError


def build_bess_fits(
    *,
    objname: str,
    observer: str,
    date_obs: str,
    exptime_s: float,
    wavelength_nm: np.ndarray,
    flux: np.ndarray,
    site: str = "AstroCitizen",
    instrument: str = "AstroCitizen-spec",
    telescop: str = "AstroCitizen",
    ra_deg: float | None = None,
    dec_deg: float | None = None,
    bss_esrp: float | None = None,
) -> fits.PrimaryHDU:
    """Constroi HDU 1D calibrado em comprimento de onda (nm -> Angstrom no WCS)."""
    wave = np.asarray(wavelength_nm, dtype=float)
    flx = np.asarray(flux, dtype=float)
    if wave.ndim != 1 or flx.ndim != 1 or len(wave) != len(flx) or len(wave) < 2:
        raise DomainError("espectro 1D invalido (wave/flux)")
    wave_a = wave * 10.0
    crval = float(wave_a[0])
    cdelt = float(wave_a[1] - wave_a[0])
    hdu = fits.PrimaryHDU(data=flx.astype(np.float32))
    hdr = hdu.header
    hdr["OBJNAME"] = objname[:68]
    hdr["OBSERVER"] = observer[:68]
    hdr["DATE-OBS"] = date_obs
    hdr["EXPTIME"] = float(exptime_s)
    hdr["BSS_SITE"] = site[:68]
    hdr["BSS_INST"] = instrument[:68]
    hdr["TELESCOP"] = telescop[:68]
    hdr["CRVAL1"] = crval
    hdr["CDELT1"] = cdelt
    hdr["CRPIX1"] = 1.0
    hdr["CTYPE1"] = "WAVE"
    hdr["CUNIT1"] = "Angstrom"
    if ra_deg is not None:
        hdr["RA"] = float(ra_deg)
    if dec_deg is not None:
        hdr["DEC"] = float(dec_deg)
    if bss_esrp is not None:
        hdr["BSS_ESRP"] = float(bss_esrp)
    hdr["ORIGIN"] = "AstroCitizen/0.0.1"
    hdr["COMMENT"] = "BeSS-oriented 1D; upload via http://basebe.obspm.fr/"
    return hdu


def write_bess_fits(path: Path, **kwargs: Any) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    hdu = build_bess_fits(**kwargs)
    hdu.writeto(path, overwrite=True)
    return path


def annotate_existing_fits(
    src: Path,
    dest: Path,
    *,
    observer: str,
    site: str | None = None,
    instrument: str | None = None,
) -> Path:
    """Copia FITS 1D e garante OBSERVER / BSS_* minimos."""
    src = Path(src)
    if not src.is_file():
        raise DomainError(f"FITS nao encontrado: {src}")
    with fits.open(src) as hdul:
        hdu = hdul[0].copy()
        hdr = hdu.header
        hdr["OBSERVER"] = observer[:68]
        if site:
            hdr["BSS_SITE"] = site[:68]
        if instrument:
            hdr["BSS_INST"] = instrument[:68]
        if "ORIGIN" not in hdr:
            hdr["ORIGIN"] = "AstroCitizen/0.0.1"
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        hdu.writeto(dest, overwrite=True)
    return dest
