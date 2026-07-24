"""Resolver VizieR (CDS ASU) — nome/cone → linha de catálogo (AC-212)."""

from __future__ import annotations

from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from astrocitizen.shared.errors import DomainError, NotFoundError

_DEFAULT_TIMEOUT_S = 45.0
# Gaia DR3 em VizieR — útil para mag G + source_id sem TAP Gaia
_DEFAULT_SOURCE = "I/355/gaiadr3"
_ASU_BASE = "https://vizier.cds.unistra.fr/viz-bin/asu-tsv"


def _parse_asu_tsv(raw: str) -> list[dict[str, str]]:
    """Parse resposta ASU TSV (linhas # comentário; tab-separated)."""
    lines = [ln for ln in raw.splitlines() if ln.strip()]
    data_lines = [ln for ln in lines if not ln.startswith("#")]
    if len(data_lines) < 2:
        return []
    headers = [h.strip() for h in data_lines[0].split("\t")]
    rows: list[dict[str, str]] = []
    for ln in data_lines[1:]:
        if ln.startswith("---"):
            continue
        parts = ln.split("\t")
        if len(parts) < 2:
            continue
        row = {
            headers[i]: parts[i].strip()
            for i in range(min(len(headers), len(parts)))
            if headers[i]
        }
        rows.append(row)
    return rows


def _float_field(row: dict[str, str], *keys: str) -> float | None:
    for k in keys:
        raw = row.get(k)
        if raw is None or raw == "" or raw == "---":
            continue
        try:
            return float(raw)
        except ValueError:
            continue
    return None


def row_to_payload(row: dict[str, str], *, query: str, source: str) -> dict[str, Any]:
    ra = _float_field(row, "RA_ICRS", "RAJ2000", "RA_d", "_RAJ2000", "ra")
    dec = _float_field(row, "DE_ICRS", "DEJ2000", "DEC_d", "_DEJ2000", "dec")
    if ra is None or dec is None:
        raise DomainError("VizieR sem RA/Dec validos", rule_id="AC-212")
    source_id = (
        row.get("Source") or row.get("source_id") or row.get("GaiaDR3") or ""
    ).strip() or None
    gmag = _float_field(row, "Gmag", "phot_g_mean_mag", "G")
    external_ids: dict[str, Any] = {
        "vizier": source,
        "source": "vizier",
    }
    if source_id:
        external_ids["gaia_source_id"] = source_id
        external_ids["vizier_id"] = source_id
    if gmag is not None:
        external_ids["gmag"] = gmag
        # mag_max so para tie-break se VSX nao tiver mag
        external_ids.setdefault("mag_max", gmag)
    desig = source_id or query
    return {
        "ra_deg": ra,
        "dec_deg": dec,
        "designation": desig,
        "external_ids": external_ids,
    }


class VizierResolver:
    """Consulta VizieR ASU (TSV) por nome ou cone."""

    def __init__(
        self,
        *,
        timeout_s: float = _DEFAULT_TIMEOUT_S,
        opener: Any | None = None,
        source: str = _DEFAULT_SOURCE,
        base_url: str = _ASU_BASE,
        radius_arcsec: float = 5.0,
    ) -> None:
        self.timeout_s = timeout_s
        self._opener = opener
        self.source = source
        self.base_url = base_url
        self.radius_arcsec = radius_arcsec

    def resolve(self, name: str) -> dict[str, Any]:
        ident = (name or "").strip()
        if not ident:
            raise DomainError("nome VizieR vazio", rule_id="AC-212")
        params = {
            "-source": self.source,
            "-c": ident,
            "-out.max": "1",
            "-out.add": "_r",
            "-sort": "_r",
        }
        raw = self._fetch(params)
        rows = _parse_asu_tsv(raw)
        if not rows:
            raise NotFoundError(f"VizieR nao encontrou: {ident}")
        return row_to_payload(rows[0], query=ident, source=self.source)

    def resolve_near(
        self, ra_deg: float, dec_deg: float, *, radius_arcsec: float | None = None
    ) -> dict[str, Any]:
        rad = radius_arcsec if radius_arcsec is not None else self.radius_arcsec
        params = {
            "-source": self.source,
            "-c": f"{ra_deg} {dec_deg}",
            "-c.rd": f"{rad / 3600.0}",
            "-out.max": "1",
            "-out.add": "_r",
            "-sort": "_r",
        }
        raw = self._fetch(params)
        rows = _parse_asu_tsv(raw)
        if not rows:
            raise NotFoundError(
                f"VizieR cone vazio em {ra_deg:.5f},{dec_deg:.5f}"
            )
        return row_to_payload(
            rows[0], query=f"{ra_deg},{dec_deg}", source=self.source
        )

    def _fetch(self, params: dict[str, str]) -> str:
        url = f"{self.base_url}?{urlencode(params)}"
        if self._opener is not None:
            return self._opener(url)
        req = Request(url, headers={"User-Agent": "AstroCitizen/0.0.1 (VizieR)"})
        try:
            with urlopen(req, timeout=self.timeout_s) as resp:  # noqa: S310
                return resp.read().decode("utf-8", errors="replace")
        except HTTPError as exc:
            raise DomainError(f"VizieR HTTP {exc.code}", rule_id="AC-212") from exc
        except URLError as exc:
            raise DomainError(
                f"VizieR rede indisponivel: {exc.reason}", rule_id="AC-212"
            ) from exc
