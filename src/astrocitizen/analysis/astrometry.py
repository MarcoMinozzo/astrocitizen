"""Medidas astrometricas (esqueleto PO-C01/C02 / inicio AC-110/111)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord
from astropy.io import fits

from astrocitizen.adapters.fs import LocalArtifactStore
from astrocitizen.analysis.photometry import aperture_sum, centroid
from astrocitizen.reduction.models import AnalysisProduct
from astrocitizen.shared.errors import DomainError
from astrocitizen.shared.ids import new_id
from astrocitizen.shared.timeutil import utc_now_iso


def pixel_to_radec_tangent(
    x: float,
    y: float,
    *,
    ra0_deg: float,
    dec0_deg: float,
    crpix1: float,
    crpix2: float,
    scale_arcsec: float,
    pa_deg: float = 0.0,
) -> tuple[float, float]:
    """Conversao tan-plane simples (sem plate-solve externo)."""
    if scale_arcsec <= 0:
        raise DomainError("scale_arcsec deve ser > 0")
    dx = (x - crpix1) * scale_arcsec
    dy = (y - crpix2) * scale_arcsec
    pa = np.deg2rad(pa_deg)
    east = dx * np.cos(pa) - dy * np.sin(pa)
    north = dx * np.sin(pa) + dy * np.cos(pa)
    sep = float(np.hypot(east, north)) * u.arcsec
    posang = float(np.arctan2(east, north)) * u.rad
    center = SkyCoord(ra=ra0_deg * u.deg, dec=dec0_deg * u.deg)
    sky = center.directional_offset_by(posang, sep)
    return float(sky.ra.deg), float(sky.dec.deg)


def pixel_to_radec_wcs(hdr: fits.Header, x: float, y: float) -> tuple[float, float] | None:
    """Tenta WCS do header; None se incompleto."""
    if "CRVAL1" not in hdr and "CTYPE1" not in hdr:
        return None
    try:
        from astropy.wcs import WCS

        wcs = WCS(hdr)
        if wcs.naxis < 2:
            return None
        sky = wcs.pixel_to_world(x, y)
        if isinstance(sky, SkyCoord):
            return float(sky.ra.deg), float(sky.dec.deg)
        if hasattr(sky, "ra"):
            return float(sky.ra.deg), float(sky.dec.deg)
    except Exception:
        return None
    return None


class MeasureAstrometry:
    """Produto astrometry: centroide + RA/Dec (WCS ou tan-plane)."""

    def __init__(self, archive: Any, store: LocalArtifactStore) -> None:
        self.archive = archive
        self.store = store

    def execute(
        self,
        *,
        workspace_id: UUID,
        fits_uri: str,
        x: float,
        y: float,
        ra0_deg: float | None = None,
        dec0_deg: float | None = None,
        scale_arcsec: float | None = None,
        pa_deg: float = 0.0,
        crpix1: float | None = None,
        crpix2: float | None = None,
        designation: str | None = None,
        band: str = "R",
        nonsidereal: bool = False,
        program_id: UUID | None = None,
        observation_id: UUID | None = None,
        t_utc: str | None = None,
        r_ap: float = 5.0,
    ) -> AnalysisProduct:
        path = self.store.resolve(fits_uri)
        with fits.open(path) as hdul:
            data = np.asarray(hdul[0].data, dtype=np.float64)
            hdr = hdul[0].header
        cx, cy = centroid(data, x, y)
        flux, err = aperture_sum(data, cx, cy, r_ap=r_ap)
        mag = None
        if flux > 0:
            mag = float(25.0 - 2.5 * np.log10(flux))

        ra_dec = pixel_to_radec_wcs(hdr, cx, cy)
        method = "wcs"
        if ra_dec is None:
            if ra0_deg is None or dec0_deg is None or scale_arcsec is None:
                raise DomainError(
                    "sem WCS no FITS: passe --ra0 --dec0 --scale-arcsec"
                )
            h, w = data.shape
            ra_dec = pixel_to_radec_tangent(
                cx,
                cy,
                ra0_deg=ra0_deg,
                dec0_deg=dec0_deg,
                crpix1=crpix1 if crpix1 is not None else (w - 1) / 2.0,
                crpix2=crpix2 if crpix2 is not None else (h - 1) / 2.0,
                scale_arcsec=scale_arcsec,
                pa_deg=pa_deg,
            )
            method = "tangent"
        ra_deg, dec_deg = ra_dec
        when = t_utc or hdr.get("DATE-OBS") or utc_now_iso()
        name = designation or hdr.get("OBJECT") or "NEO"

        product = AnalysisProduct(
            id=new_id(),
            workspace_id=workspace_id,
            program_id=program_id,
            product_type="astrometry",
            version_num=1,
            is_publishable=False,
            parameters={
                "method": method,
                "x0": x,
                "y0": y,
                "centroid": [cx, cy],
                "fits_uri": fits_uri,
                "nonsidereal": nonsidereal,
                "designation": name,
                "band": band,
                "scale_arcsec": scale_arcsec,
                "pa_deg": pa_deg,
            },
            summary={
                "ra_deg": ra_deg,
                "dec_deg": dec_deg,
                "mag": mag,
                "epoch_utc": when,
                "flux": flux,
            },
            state="ready",
        )
        product = self.archive.save_analysis_product(product)
        if observation_id:
            self.archive.link_product_observation(product.id, observation_id)
        self.archive.save_measurement_points(
            product.id,
            [
                {
                    "t_utc": when,
                    "sequence_index": 0,
                    "x": ra_deg,
                    "y": dec_deg,
                    "y_err": None,
                    "band": band,
                    "meta": {
                        "ra_deg": ra_deg,
                        "dec_deg": dec_deg,
                        "mag": mag,
                        "cx": cx,
                        "cy": cy,
                        "flux": flux,
                        "flux_err": err,
                        "designation": name,
                    },
                }
            ],
        )
        return product
