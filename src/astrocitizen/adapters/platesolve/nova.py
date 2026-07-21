"""Backend remoto: nova.astrometry.net (AC-110)."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from astropy.io import fits
from astropy.wcs import WCS

from astrocitizen.adapters.platesolve.synthetic import SyntheticPlateSolver
from astrocitizen.adapters.platesolve.wcs_io import wcs_summary
from astrocitizen.ports.platesolve import PlateSolveResult
from astrocitizen.shared.errors import DomainError

NOVA_API = "https://nova.astrometry.net/api"


class NovaAstrometryNetSolver:
    """Cliente HTTP minimo da Nova API (login -> upload -> poll -> wcs).

    Com dry_run=True (default) usa SyntheticPlateSolver (sem rede).
    """

    def __init__(
        self,
        *,
        api_key: str,
        endpoint: str = NOVA_API,
        dry_run: bool = True,
        poll_interval_s: float = 3.0,
        timeout_s: float = 180.0,
    ) -> None:
        self.api_key = api_key
        self.endpoint = endpoint.rstrip("/")
        self.dry_run = dry_run
        self.poll_interval_s = poll_interval_s
        self.timeout_s = timeout_s

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode()
        req = Request(
            f"{self.endpoint}{path}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())

    def _login(self) -> str:
        data = self._post_json("/login", {"apikey": self.api_key})
        if data.get("status") != "success" or not data.get("session"):
            raise DomainError(f"nova login falhou: {data}")
        return str(data["session"])

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
        fits_path = Path(fits_path)
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        if self.dry_run:
            syn = SyntheticPlateSolver(
                default_scale_arcsec=(
                    0.5
                    * (
                        (scale_low_arcsec or 1.0)
                        + (scale_high_arcsec or scale_low_arcsec or 1.0)
                    )
                )
            )
            result = syn.solve(
                fits_path,
                out_dir=out_dir,
                ra_hint_deg=ra_hint_deg,
                dec_hint_deg=dec_hint_deg,
                radius_deg=radius_deg,
                scale_low_arcsec=scale_low_arcsec,
                scale_high_arcsec=scale_high_arcsec,
                timeout_s=timeout_s,
            )
            result.backend = "nova-dry-run"
            result.meta["dry_run"] = True
            result.meta["endpoint"] = self.endpoint
            return result

        if not self.api_key or self.api_key == "dry-run-key":
            raise DomainError("nova real requer api_key (credentials astrometrynet)")

        try:
            session = self._login()
        except (URLError, OSError, json.JSONDecodeError) as exc:
            raise DomainError(f"nova login erro: {exc}") from exc

        # Multipart upload is verbose; use url_upload with file:// not supported.
        # Minimal: send base64 via request-json + file upload endpoint pattern.
        import base64

        b64 = base64.b64encode(fits_path.read_bytes()).decode("ascii")
        req_payload: dict[str, Any] = {
            "session": session,
            "allow_commercial_use": "d",
            "allow_modifications": "d",
            "publicly_visible": "n",
        }
        if ra_hint_deg is not None and dec_hint_deg is not None:
            req_payload["center_ra"] = ra_hint_deg
            req_payload["center_dec"] = dec_hint_deg
            if radius_deg is not None:
                req_payload["radius"] = radius_deg
        if scale_low_arcsec is not None:
            req_payload["scale_lower"] = scale_low_arcsec
            req_payload["scale_units"] = "arcsecperpix"
        if scale_high_arcsec is not None:
            req_payload["scale_upper"] = scale_high_arcsec
            req_payload["scale_units"] = "arcsecperpix"

        boundary = "----AstroCitizenNova"
        parts = []
        parts.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="request-json"\r\n\r\n'
                f"{json.dumps(req_payload)}\r\n"
            ).encode()
        )
        parts.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="file"; '
                f'filename="{fits_path.name}"\r\n'
                f"Content-Type: application/fits\r\n\r\n"
            ).encode()
            + fits_path.read_bytes()
            + b"\r\n"
        )
        # Prefer binary file part over b64; drop unused b64 if file sent
        _ = b64
        parts.append(f"--{boundary}--\r\n".encode())
        body = b"".join(parts)
        upload_req = Request(
            f"{self.endpoint}/upload",
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        try:
            with urlopen(upload_req, timeout=120) as resp:
                up = json.loads(resp.read().decode())
        except (URLError, OSError, json.JSONDecodeError) as exc:
            raise DomainError(f"nova upload erro: {exc}") from exc
        if up.get("status") != "success":
            raise DomainError(f"nova upload falhou: {up}")
        sub_id = up.get("subid")
        if sub_id is None:
            raise DomainError(f"nova sem subid: {up}")

        deadline = time.time() + max(timeout_s, self.timeout_s)
        job_id = None
        while time.time() < deadline:
            try:
                with urlopen(
                    f"{self.endpoint}/submissions/{sub_id}", timeout=30
                ) as resp:
                    sub = json.loads(resp.read().decode())
            except (URLError, OSError, json.JSONDecodeError):
                time.sleep(self.poll_interval_s)
                continue
            jobs = sub.get("jobs") or []
            if jobs and jobs[0]:
                job_id = jobs[0]
                break
            time.sleep(self.poll_interval_s)
        if job_id is None:
            raise DomainError("nova: timeout a espera de job")

        while time.time() < deadline:
            try:
                with urlopen(f"{self.endpoint}/jobs/{job_id}", timeout=30) as resp:
                    job = json.loads(resp.read().decode())
            except (URLError, OSError, json.JSONDecodeError):
                time.sleep(self.poll_interval_s)
                continue
            status = job.get("status")
            if status == "success":
                break
            if status == "failure":
                raise DomainError(f"nova job falhou: {job}")
            time.sleep(self.poll_interval_s)
        else:
            raise DomainError("nova: timeout no job")

        wcs_url = f"https://nova.astrometry.net/wcs_file/{job_id}"
        dest = out_dir / f"{fits_path.stem}_wcs.fits"
        try:
            with urlopen(wcs_url, timeout=60) as resp:
                dest.write_bytes(resp.read())
        except (URLError, OSError) as exc:
            raise DomainError(f"nova download wcs erro: {exc}") from exc

        # Nova wcs_file is often header-only; merge onto original image if needed
        with fits.open(dest) as whdul, fits.open(fits_path) as src:
            if whdul[0].data is None and src[0].data is not None:
                hdu = src[0].copy()
                hdu.header.update(whdul[0].header)
                hdu.writeto(dest, overwrite=True)

        with fits.open(dest) as hdul:
            data = hdul[0].data
            hdr = hdul[0].header
            if data is None:
                raise DomainError("nova WCS sem imagem")
            ny, nx = data.shape[-2], data.shape[-1]
            wcs = WCS(hdr)
        summ = wcs_summary(wcs, ny=ny, nx=nx)
        return PlateSolveResult(
            ra_center_deg=summ["ra_center_deg"],
            dec_center_deg=summ["dec_center_deg"],
            scale_arcsec=summ["scale_arcsec"],
            backend="nova",
            wcs_fits_path=dest,
            meta={"job_id": job_id, "sub_id": sub_id},
        )
