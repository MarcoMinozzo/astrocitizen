"""Provider BeSS — wrapper FITS 1D (D-012)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from astrocitizen.contribution.bess import write_bess_fits
from astrocitizen.domain.observation import Spectrum
from astrocitizen.integrations.base import BaseObservatoryProvider
from astrocitizen.shared.errors import DomainError


class BessProvider(BaseObservatoryProvider):
    name = "bess"
    features = frozenset({"prepare_spectrum"})

    def prepare_spectrum(
        self, spectrum: Spectrum, *, out_path: Path, **kwargs: Any
    ) -> Path:
        if len(spectrum.wavelength) < 2 or len(spectrum.flux) < 2:
            raise DomainError("BeSS: spectrum.wavelength/flux insuficientes", rule_id="D-012")
        date_obs = kwargs.get("date_obs") or spectrum.extra.get("date_obs")
        if not date_obs:
            raise DomainError("BeSS: date_obs obrigatorio", rule_id="D-012")
        exptime = kwargs.get("exptime_s")
        if exptime is None:
            exptime = spectrum.extra.get("exptime_s", spectrum.fits_header.get("EXPTIME"))
        if exptime is None:
            raise DomainError("BeSS: exptime_s obrigatorio", rule_id="D-012")
        return write_bess_fits(
            Path(out_path),
            objname=spectrum.object_name,
            observer=str(spectrum.observer or kwargs.get("observer") or "AstroCitizen"),
            date_obs=str(date_obs),
            exptime_s=float(exptime),
            wavelength_nm=np.asarray(spectrum.wavelength, dtype=float),
            flux=np.asarray(spectrum.flux, dtype=float),
            instrument=str(spectrum.instrument or kwargs.get("instrument") or "AstroCitizen-spec"),
            ra_deg=kwargs.get("ra_deg") or spectrum.extra.get("ra_deg"),
            dec_deg=kwargs.get("dec_deg") or spectrum.extra.get("dec_deg"),
        )
