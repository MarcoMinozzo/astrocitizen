"""Fotometria de abertura simples + centroide (inicio E9 / AC-090/091)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID

import numpy as np
from astropy.io import fits

from astrocitizen.adapters.fs import LocalArtifactStore
from astrocitizen.reduction.models import AnalysisProduct
from astrocitizen.shared.errors import DomainError
from astrocitizen.shared.ids import new_id
from astrocitizen.shared.timeutil import utc_now_iso


def centroid(data: np.ndarray, x0: float, y0: float, box: int = 7) -> tuple[float, float]:
    """Centroide de intensidade num box ao redor de (x0,y0)."""
    h, w = data.shape
    x0i, y0i = int(round(x0)), int(round(y0))
    x1, x2 = max(0, x0i - box), min(w, x0i + box + 1)
    y1, y2 = max(0, y0i - box), min(h, y0i + box + 1)
    cut = data[y1:y2, x1:x2]
    cut = cut - np.median(cut)
    cut = np.clip(cut, 0, None)
    total = float(cut.sum())
    if total <= 0:
        return float(x0), float(y0)
    yy, xx = np.mgrid[y1:y2, x1:x2]
    return float((xx * cut).sum() / total), float((yy * cut).sum() / total)


def aperture_sum(
    data: np.ndarray,
    x: float,
    y: float,
    r_ap: float = 5.0,
    r_in: float = 8.0,
    r_out: float = 12.0,
) -> tuple[float, float]:
    """Fluxo de abertura com anel de ceu; devolve (flux, err_approx)."""
    h, w = data.shape
    yy, xx = np.mgrid[0:h, 0:w]
    rr = np.sqrt((xx - x) ** 2 + (yy - y) ** 2)
    ap = rr <= r_ap
    sky = (rr >= r_in) & (rr <= r_out)
    sky_vals = data[sky]
    if sky_vals.size == 0:
        sky_med = 0.0
        sky_std = float(np.std(data))
    else:
        sky_med = float(np.median(sky_vals))
        sky_std = float(np.std(sky_vals))
    n_ap = int(ap.sum())
    flux = float(data[ap].sum() - sky_med * n_ap)
    err = sky_std * np.sqrt(n_ap) if n_ap else 0.0
    return flux, float(err)


def flux_to_mag(flux: float, zp: float = 25.0) -> float | None:
    if flux <= 0:
        return None
    return float(zp - 2.5 * np.log10(flux))


class AperturePhotometry:
    """Gera produto light_curve (1+ pontos) a partir de frame calibrado."""

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
        band: str = "V",
        program_id: UUID | None = None,
        observation_id: UUID | None = None,
        comp_xy: tuple[float, float] | None = None,
        t_utc: str | None = None,
        r_ap: float = 5.0,
    ) -> AnalysisProduct:
        path = self.store.resolve(fits_uri)
        with fits.open(path) as hdul:
            data = np.asarray(hdul[0].data, dtype=np.float64)
            hdr = hdul[0].header
        cx, cy = centroid(data, x, y)
        flux, err = aperture_sum(data, cx, cy, r_ap=r_ap)
        mag = flux_to_mag(flux)
        dmag = None
        if comp_xy is not None:
            ccx, ccy = centroid(data, comp_xy[0], comp_xy[1])
            cflux, _ = aperture_sum(data, ccx, ccy, r_ap=r_ap)
            cmag = flux_to_mag(cflux)
            if mag is not None and cmag is not None:
                dmag = mag - cmag

        when = t_utc or hdr.get("DATE-OBS") or utc_now_iso()
        product = AnalysisProduct(
            id=new_id(),
            workspace_id=workspace_id,
            program_id=program_id,
            product_type="light_curve",
            version_num=1,
            is_publishable=False,
            parameters={
                "method": "aperture",
                "r_ap": r_ap,
                "x0": x,
                "y0": y,
                "centroid": [cx, cy],
                "fits_uri": fits_uri,
                "band": band,
            },
            summary={
                "n_points": 1,
                "mag": mag,
                "dmag": dmag,
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
                    "x": 0.0,
                    "y": dmag if dmag is not None else (mag if mag is not None else flux),
                    "y_err": err / flux * 1.0857 if flux > 0 and mag is not None else err,
                    "band": band,
                    "meta": {"flux": flux, "mag": mag, "dmag": dmag, "cx": cx, "cy": cy},
                }
            ],
        )
        return product
