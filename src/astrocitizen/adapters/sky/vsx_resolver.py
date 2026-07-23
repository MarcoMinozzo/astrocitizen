"""Resolver VSX (Variable Star Index) — consulta oficial AAVSO (AC-096)."""

from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from astrocitizen.adapters.aavso_portal import VSX_OBJECT_API
from astrocitizen.shared.errors import DomainError, NotFoundError

_DEFAULT_TIMEOUT_S = 30.0


def _parse_mag_field(raw: str | None) -> float | None:
    """Extrai numero de campos tipo '7.7 V' ou '12.4'."""
    if not raw:
        return None
    token = str(raw).strip().split()[0]
    try:
        return float(token)
    except ValueError:
        return None


class VsxResolver:
    """Resolve nome/AUID via VSX object API (JSON)."""

    def __init__(
        self,
        *,
        timeout_s: float = _DEFAULT_TIMEOUT_S,
        opener: Any | None = None,
    ) -> None:
        self.timeout_s = timeout_s
        self._opener = opener  # injectavel para testes

    def resolve(self, name: str) -> dict[str, Any]:
        ident = (name or "").strip()
        if not ident:
            raise DomainError("nome VSX vazio", rule_id="AC-096")
        url = VSX_OBJECT_API.format(ident=quote(ident, safe=""))
        raw = self._fetch(url)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise DomainError(
                "VSX devolveu JSON invalido", rule_id="AC-096"
            ) from exc
        obj = data.get("VSXObject") if isinstance(data, dict) else None
        if not isinstance(obj, dict) or not obj:
            raise NotFoundError(f"VSX nao encontrou: {ident}")
        try:
            ra = float(obj["RA2000"])
            dec = float(obj["Declination2000"])
        except (KeyError, TypeError, ValueError) as exc:
            raise DomainError(
                f"VSX sem RA/Dec validos para {ident}", rule_id="AC-096"
            ) from exc
        auid = str(obj.get("AUID") or "").strip() or None
        vsx_name = str(obj.get("Name") or ident).strip()
        var_type = str(obj.get("VariabilityType") or "").strip() or None
        period_raw = obj.get("Period")
        period: float | None
        try:
            period = float(period_raw) if period_raw not in (None, "") else None
        except (TypeError, ValueError):
            period = None
        max_mag = _parse_mag_field(obj.get("MaxMag"))
        min_mag = _parse_mag_field(obj.get("MinMag"))
        oid = str(obj.get("OID") or "").strip() or None
        external_ids: dict[str, Any] = {
            "vsx": vsx_name,
            "source": "vsx",
        }
        if auid:
            external_ids["auid"] = auid
        if oid:
            external_ids["vsx_oid"] = oid
        if var_type:
            external_ids["variability_type"] = var_type
        if period is not None:
            external_ids["period"] = period
        if max_mag is not None:
            external_ids["mag_max"] = max_mag
        if min_mag is not None:
            external_ids["mag_min"] = min_mag
        return {
            "ra_deg": ra,
            "dec_deg": dec,
            "designation": vsx_name,
            "external_ids": external_ids,
        }

    def _fetch(self, url: str) -> str:
        if self._opener is not None:
            return self._opener(url)
        req = Request(url, headers={"User-Agent": "AstroCitizen/0.0.1 (VSX)"})
        try:
            with urlopen(req, timeout=self.timeout_s) as resp:  # noqa: S310
                return resp.read().decode("utf-8", errors="replace")
        except HTTPError as exc:
            if exc.code == 404:
                raise NotFoundError(f"VSX HTTP 404: {url}") from exc
            raise DomainError(
                f"VSX HTTP {exc.code}", rule_id="AC-096"
            ) from exc
        except URLError as exc:
            raise DomainError(
                f"VSX rede indisponivel: {exc.reason}", rule_id="AC-096"
            ) from exc
