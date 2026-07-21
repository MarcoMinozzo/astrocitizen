"""Backend local: astrometry.net solve-field (CLI)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from astropy.io import fits
from astropy.wcs import WCS

from astrocitizen.adapters.platesolve.wcs_io import wcs_summary
from astrocitizen.ports.platesolve import PlateSolveResult
from astrocitizen.shared.errors import DomainError


class SolveFieldPlateSolver:
    """Wrapper de `solve-field` (pacote astrometry.net)."""

    def __init__(self, *, binary: str = "solve-field") -> None:
        self.binary = binary

    def available(self) -> bool:
        return shutil.which(self.binary) is not None

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
        if not self.available():
            raise DomainError(
                f"{self.binary} nao encontrado no PATH; "
                "instale astrometry.net ou use --backend synthetic|nova"
            )
        fits_path = Path(fits_path).resolve()
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        new_fits = out_dir / f"{fits_path.stem}_wcs.fits"
        cmd = [
            self.binary,
            "--no-plots",
            "--overwrite",
            "--dir",
            str(out_dir),
            "--new-fits",
            str(new_fits),
        ]
        if scale_low_arcsec is not None and scale_high_arcsec is not None:
            cmd.extend(
                [
                    "--scale-units",
                    "arcsecperpix",
                    "--scale-low",
                    str(scale_low_arcsec),
                    "--scale-high",
                    str(scale_high_arcsec),
                ]
            )
        if ra_hint_deg is not None and dec_hint_deg is not None:
            cmd.extend(["--ra", str(ra_hint_deg), "--dec", str(dec_hint_deg)])
            if radius_deg is not None:
                cmd.extend(["--radius", str(radius_deg)])
        cmd.append(str(fits_path))

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_s,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise DomainError(f"solve-field timeout ({timeout_s}s)") from exc
        if proc.returncode != 0 or not new_fits.is_file():
            err = (proc.stderr or proc.stdout or "")[-800:]
            raise DomainError(f"solve-field falhou (code={proc.returncode}): {err}")

        with fits.open(new_fits) as hdul:
            data = hdul[0].data
            hdr = hdul[0].header
            ny, nx = data.shape[-2], data.shape[-1]
            wcs = WCS(hdr)
        summ = wcs_summary(wcs, ny=ny, nx=nx)
        return PlateSolveResult(
            ra_center_deg=summ["ra_center_deg"],
            dec_center_deg=summ["dec_center_deg"],
            scale_arcsec=summ["scale_arcsec"],
            backend="solve-field",
            wcs_fits_path=new_fits,
            meta={"returncode": proc.returncode},
        )
