"""Backend synthetic: injeta WCS TAN a partir de hints (CI / offline)."""

from __future__ import annotations

from pathlib import Path

from astropy.io import fits

from astrocitizen.adapters.platesolve.wcs_io import build_tan_wcs, write_fits_with_wcs
from astrocitizen.ports.platesolve import PlateSolveResult
from astrocitizen.shared.errors import DomainError


class SyntheticPlateSolver:
    """Plate-solve deterministico para testes e desenvolvimento sem solver externo."""

    def __init__(self, *, default_scale_arcsec: float = 1.0, pa_deg: float = 0.0) -> None:
        self.default_scale_arcsec = default_scale_arcsec
        self.pa_deg = pa_deg

    def solve(
        self,
        fits_path: Path,
        *,
        out_dir: Path,
        ra_hint_deg: float | None = None,
        dec_hint_deg: float | None = None,
        radius_deg: float | None = None,
        scale_low_arcsec: float | None = None,
        scale_high_arcsec: float | None = None,
        timeout_s: float = 120.0,
    ) -> PlateSolveResult:
        _ = radius_deg, timeout_s
        if ra_hint_deg is None or dec_hint_deg is None:
            raise DomainError(
                "synthetic plate-solve requer --ra-hint e --dec-hint"
            )
        if scale_low_arcsec is not None and scale_high_arcsec is not None:
            scale = 0.5 * (float(scale_low_arcsec) + float(scale_high_arcsec))
        elif scale_low_arcsec is not None:
            scale = float(scale_low_arcsec)
        else:
            scale = float(self.default_scale_arcsec)
        fits_path = Path(fits_path)
        with fits.open(fits_path) as hdul:
            data = hdul[0].data
            if data is None or getattr(data, "ndim", 0) < 2:
                raise DomainError("FITS 2D requerido")
            ny, nx = data.shape[-2], data.shape[-1]
        crpix1 = (nx - 1) / 2.0 + 1.0  # FITS 1-indexed
        crpix2 = (ny - 1) / 2.0 + 1.0
        wcs = build_tan_wcs(
            ra_deg=ra_hint_deg,
            dec_deg=dec_hint_deg,
            scale_arcsec=scale,
            crpix1=crpix1,
            crpix2=crpix2,
            pa_deg=self.pa_deg,
        )
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        dest = out_dir / f"{fits_path.stem}_wcs.fits"
        write_fits_with_wcs(
            fits_path,
            dest,
            wcs,
            extra_cards={"PLTSOLVD": True, "ASTROMET": "synthetic"},
        )
        return PlateSolveResult(
            ra_center_deg=float(ra_hint_deg),
            dec_center_deg=float(dec_hint_deg),
            scale_arcsec=scale,
            backend="synthetic",
            orientation_deg=float(self.pa_deg),
            wcs_fits_path=dest,
            meta={"nx": nx, "ny": ny},
        )
