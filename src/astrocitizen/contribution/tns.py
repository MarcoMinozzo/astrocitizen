"""TNS Bulk API - AT-rep JSON + sandbox client (PO-C03)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from astrocitizen.shared.errors import DomainError

TNS_SANDBOX = "https://sandbox.wis-tns.org"
TNS_PROD = "https://www.wis-tns.org"


def format_tns_at_report(
    *,
    ra_deg: float,
    dec_deg: float,
    groupid: int,
    reporter: str,
    discovery_mag: float,
    filter_value: str = "Clear",
    instrument_value: str = "Other",
    limiting_flux: float | None = None,
    internal_name: str | None = None,
) -> dict[str, Any]:
    """AT-rep minimo (estrutura alinhada aos manuais TNS 2.0)."""
    at0: dict[str, Any] = {
        "ra": {"value": ra_deg, "error": 1.0, "units": "arcsec"},
        "dec": {"value": dec_deg, "error": 1.0, "units": "arcsec"},
        "reporting_groupid": groupid,
        "discovery_data_source_id": groupid,
        "reporter_name": reporter,
        "non_detection": {
            "archiveid": 0,
            "archival_nondetection_limit": limiting_flux if limiting_flux is not None else 99.0,
        },
        "photometry": {
            "telescope_name": "Other",
            "instrument_name": instrument_value,
            "filter_name": filter_value,
            "flux": discovery_mag,
            "flux_error": 0.1,
            "flux_unit": "ABMag",
        },
    }
    if internal_name:
        at0["internal_name"] = internal_name
    return {"at_report": {"0": at0}}


class TnsClient:
    """Cliente TNS Bulk reports (default sandbox + dry_run)."""

    def __init__(
        self,
        *,
        api_key: str,
        user_id: str,
        sandbox: bool = True,
        timeout_s: float = 60.0,
    ) -> None:
        self.api_key = api_key
        self.user_id = user_id
        self.base = TNS_SANDBOX if sandbox else TNS_PROD
        self.timeout_s = timeout_s

    def submit_report(
        self,
        report: dict[str, Any],
        *,
        dry_run: bool = True,
    ) -> dict[str, Any]:
        url = f"{self.base}/api/set/object"
        meta: dict[str, Any] = {
            "provider": "tns",
            "endpoint": url,
            "sandbox": self.base == TNS_SANDBOX,
            "dry_run": dry_run,
        }
        if dry_run:
            meta["status"] = "dry_run"
            meta["payload_preview"] = json.dumps(report)[:500]
            return meta
        form = urlencode(
            {
                "api_key": self.api_key,
                "data": json.dumps(report),
            }
        ).encode()
        req = Request(
            url,
            data=form,
            method="POST",
            headers={
                "User-Agent": (
                    f'tns_marker{{"tns_id":"{self.user_id}",'
                    f'"type":"bot","name":"AstroCitizen"}}'
                ),
                "Content-Type": "application/x-www-form-urlencoded",
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
            raise DomainError(f"TNS submit falhou: {exc}") from exc


def write_tns_report(path: Path, report: dict[str, Any]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return path
