"""MPC ADES PSV export + submit HTTP (AC-112)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from astrocitizen.shared.errors import DomainError

MPC_SUBMIT_PSV = "https://minorplanetcenter.net/submit_psv"


def format_ades_psv(
    *,
    observatory_code: str,
    designation: str,
    observations: list[dict[str, Any]],
    submitter: str = "AstroCitizen",
) -> str:
    """ADES PSV minimo (pipe-separated) para uma designacao.

    Cada obs: epoch_utc (ISO), ra_deg, dec_deg, optional mag, band, ra_err_arcsec, dec_err_arcsec.
    """
    lines = [
        "# version=2017",
        f"# submitter={submitter}",
        f"# observatory={observatory_code}",
        "#",
        "permID|provID|obsTime|ra|dec|mag|band|rmsRA|rmsDec|astCat|mode|stn",
    ]
    for o in observations:
        epoch = str(o.get("epoch_utc") or "").replace("Z", "")
        if epoch.endswith("+00:00"):
            epoch = epoch[:-6]
        ra = float(o["ra_deg"])
        dec = float(o["dec_deg"])
        mag = o.get("mag")
        mag_s = f"{float(mag):.2f}" if mag is not None else ""
        band = str(o.get("band") or "")
        rms_ra = o.get("ra_err_arcsec")
        rms_dec = o.get("dec_err_arcsec")
        rms_ra_s = f"{float(rms_ra):.3f}" if rms_ra is not None else ""
        rms_dec_s = f"{float(rms_dec):.3f}" if rms_dec is not None else ""
        # permID empty; provID = designation for NEO/unnumbered
        lines.append(
            f"|{designation}|{epoch}|{ra:.8f}|{dec:.8f}|{mag_s}|{band}|"
            f"{rms_ra_s}|{rms_dec_s}|Gaia2|CCD|{observatory_code}"
        )
    return "\n".join(lines) + "\n"


class MpcAdesSubmitter:
    """Submete ADES PSV ao MPC (default dry_run)."""

    def __init__(self, *, timeout_s: float = 60.0, endpoint: str = MPC_SUBMIT_PSV) -> None:
        self.timeout_s = timeout_s
        self.endpoint = endpoint

    def submit(
        self,
        psv_path: Path,
        *,
        email: str,
        ack: str = "AstroCitizen submission",
        obj_type: str = "NEO",
        dry_run: bool = True,
    ) -> dict[str, Any]:
        psv_path = Path(psv_path)
        if not psv_path.is_file():
            raise DomainError(f"ADES PSV nao encontrado: {psv_path}")
        body = psv_path.read_bytes()
        meta = {
            "provider": "mpc",
            "endpoint": self.endpoint,
            "obj_type": obj_type,
            "bytes": len(body),
            "dry_run": dry_run,
        }
        if dry_run:
            meta["status"] = "dry_run"
            meta["ack"] = "not sent"
            return meta
        # multipart/form-data minimal
        boundary = "----AstroCitizenBoundary7MA4YWxk"
        parts: list[bytes] = []
        fields = {
            "ack": ack,
            "ac2": email,
            "obj_type": obj_type,
        }
        for name, value in fields.items():
            parts.append(
                (
                    f"--{boundary}\r\n"
                    f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
                    f"{value}\r\n"
                ).encode()
            )
        parts.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="source"; filename="{psv_path.name}"\r\n'
                f"Content-Type: text/plain\r\n\r\n"
            ).encode()
            + body
            + b"\r\n"
        )
        parts.append(f"--{boundary}--\r\n".encode())
        data = b"".join(parts)
        req = Request(
            self.endpoint,
            data=data,
            method="POST",
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "User-Agent": "astrocitizen/0.0.1",
            },
        )
        try:
            with urlopen(req, timeout=self.timeout_s) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                meta["status"] = "submitted"
                meta["http_status"] = getattr(resp, "status", None)
                meta["response"] = raw[:2000]
                return meta
        except (URLError, TimeoutError, OSError) as exc:
            raise DomainError(f"MPC submit falhou: {exc}") from exc


def write_ades_psv(path: Path, **kwargs: Any) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(format_ades_psv(**kwargs), encoding="utf-8")
    return path
