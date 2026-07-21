"""Helpers WCS partilhados pelos adapters de plate-solve."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

from astrocitizen.shared.errors import DomainError


def build_tan_wcs(
    *,
    ra_deg: float,
    dec_deg: float,
    scale_arcsec: float,
    crpix1: float,
    crpix2: float,
    pa_deg: float = 0.0,
    flip_ra: bool = True,
) -> WCS:
    """WCS TAN simples a partir de apontamento + escala."""
    if scale_arcsec <= 0:
        raise DomainError("scale_arcsec deve ser > 0")
    scale_deg = scale_arcsec / 3600.0
    w = WCS(naxis=2)
    w.wcs.crpix = [float(crpix1), float(crpix2)]
    # CD matrix with optional RA flip (sky convention)
    pa = np.deg2rad(pa_deg)
    sx = -scale_deg if flip_ra else scale_deg
    sy = scale_deg
    cos_a, sin_a = np.cos(pa), np.sin(pa)
    w.wcs.cd = [
        [sx * cos_a, -sy * sin_a],
        [sx * sin_a, sy * cos_a],
    ]
    w.wcs.crval = [float(ra_deg), float(dec_deg)]
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    w.wcs.cunit = ["deg", "deg"]
    return w


def write_fits_with_wcs(
    src: Path,
    dest: Path,
    wcs: WCS,
    *,
    extra_cards: dict[str, Any] | None = None,
) -> Path:
    """Copia imagem e injeta header WCS."""
    src = Path(src)
    dest = Path(dest)
    if not src.is_file():
        raise DomainError(f"FITS nao encontrado: {src}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with fits.open(src) as hdul:
        hdu = hdul[0].copy()
        # drop conflicting WCS keys
        for key in list(hdu.header.keys()):
            if key.startswith(("CD1_", "CD2_", "PC1_", "PC2_", "CDELT", "CROTA")):
                del hdu.header[key]
        hdu.header.update(wcs.to_header())
        if extra_cards:
            for k, v in extra_cards.items():
                hdu.header[k] = v
        hdu.header["ORIGIN"] = "AstroCitizen/0.0.1"
        hdu.writeto(dest, overwrite=True)
    return dest


def wcs_summary(wcs: WCS, *, ny: int, nx: int) -> dict[str, float]:
    """Centro e escala aproximada a partir do WCS."""
    cx = (nx - 1) / 2.0
    cy = (ny - 1) / 2.0
    sky = wcs.pixel_to_world(cx, cy)
    ra = float(sky.ra.deg)
    dec = float(sky.dec.deg)
    # scale from CD / CDELT
    cd = getattr(wcs.wcs, "cd", None)
    if cd is not None:
        scale = float(np.sqrt(abs(np.linalg.det(cd))) * 3600.0)
    else:
        cdelt = wcs.wcs.cdelt
        scale = float(abs(cdelt[1]) * 3600.0) if cdelt is not None else 0.0
    return {"ra_center_deg": ra, "dec_center_deg": dec, "scale_arcsec": scale}
