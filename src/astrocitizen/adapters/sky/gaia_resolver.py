"""Resolver Gaia Archive TAP — cone ICRS → source_id / G / PM (AC-213)."""

from __future__ import annotations

import csv
import io
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from astrocitizen.shared.errors import DomainError, NotFoundError

_DEFAULT_TIMEOUT_S = 60.0
_TAP_SYNC = "https://gea.esac.esa.int/tap-server/tap/sync"
_DEFAULT_TABLE = "gaiadr3.gaia_source"


def _parse_csv(raw: str) -> list[dict[str, str]]:
    text = raw.strip()
    if not text:
        return []
    # TAP may prepend INFO lines; keep from header with source_id/ra
    lines = text.splitlines()
    start = 0
    for i, ln in enumerate(lines):
        low = ln.lower()
        if "source_id" in low and ("ra" in low or "dec" in low):
            start = i
            break
    buf = io.StringIO("\n".join(lines[start:]))
    reader = csv.DictReader(buf)
    return [dict(row) for row in reader if row]


def _f(row: dict[str, str], *keys: str) -> float | None:
    for k in keys:
        for cand in (k, k.lower(), k.upper()):
            if cand in row and row[cand] not in (None, "", "null"):
                try:
                    return float(row[cand])
                except ValueError:
                    continue
        # case-insensitive
        for rk, rv in row.items():
            if rk.lower() == k.lower() and rv not in (None, "", "null"):
                try:
                    return float(rv)
                except ValueError:
                    continue
    return None


def _s(row: dict[str, str], *keys: str) -> str | None:
    for k in keys:
        for rk, rv in row.items():
            if rk.lower() == k.lower() and rv not in (None, "", "null"):
                return str(rv).strip()
    return None


def row_to_payload(row: dict[str, str], *, query: str) -> dict[str, Any]:
    ra = _f(row, "ra")
    dec = _f(row, "dec")
    if ra is None or dec is None:
        raise DomainError("Gaia sem RA/Dec validos", rule_id="AC-213")
    sid = _s(row, "source_id")
    gmag = _f(row, "phot_g_mean_mag")
    parallax = _f(row, "parallax")
    pmra = _f(row, "pmra")
    pmdec = _f(row, "pmdec")
    external_ids: dict[str, Any] = {"gaia": sid or query, "source": "gaia"}
    if sid:
        external_ids["gaia_source_id"] = sid
    if gmag is not None:
        external_ids["gmag"] = gmag
        # Nao definir mag_max a partir de G — so faz sentido para a propria estrela
        # Gaia; o merge promove vmag/VSX. Cone enrich nao deve fingir mag do alvo.
    if parallax is not None:
        external_ids["parallax_mas"] = parallax
    if pmra is not None:
        external_ids["pmra"] = pmra
    if pmdec is not None:
        external_ids["pmdec"] = pmdec
    return {
        "ra_deg": ra,
        "dec_deg": dec,
        "designation": sid or query,
        "external_ids": external_ids,
    }


class GaiaResolver:
    """Consulta Gaia TAP sync (CSV) por cone ou source_id."""

    def __init__(
        self,
        *,
        timeout_s: float = _DEFAULT_TIMEOUT_S,
        opener: Any | None = None,
        tap_url: str = _TAP_SYNC,
        table: str = _DEFAULT_TABLE,
        radius_arcsec: float = 5.0,
    ) -> None:
        self.timeout_s = timeout_s
        self._opener = opener
        self.tap_url = tap_url
        self.table = table
        self.radius_arcsec = radius_arcsec

    def resolve(self, name: str) -> dict[str, Any]:
        """Aceita source_id numerico Gaia; senao NotFound (usar resolve_near)."""
        ident = (name or "").strip()
        if not ident:
            raise DomainError("nome Gaia vazio", rule_id="AC-213")
        if not ident.isdigit():
            raise NotFoundError(
                f"Gaia TAP requer source_id ou coords (nao nome livre): {ident}"
            )
        adql = (
            f"SELECT TOP 1 source_id, ra, dec, phot_g_mean_mag, parallax, pmra, pmdec "
            f"FROM {self.table} WHERE source_id = {ident}"
        )
        raw = self._fetch(adql)
        rows = _parse_csv(raw)
        if not rows:
            raise NotFoundError(f"Gaia nao encontrou source_id={ident}")
        return row_to_payload(rows[0], query=ident)

    def resolve_near(
        self, ra_deg: float, dec_deg: float, *, radius_arcsec: float | None = None
    ) -> dict[str, Any]:
        rad = (radius_arcsec if radius_arcsec is not None else self.radius_arcsec) / 3600.0
        adql = (
            f"SELECT TOP 1 source_id, ra, dec, phot_g_mean_mag, parallax, pmra, pmdec, "
            f"DISTANCE(POINT('ICRS', ra, dec), POINT('ICRS', {ra_deg}, {dec_deg})) AS dist "
            f"FROM {self.table} "
            f"WHERE 1=CONTAINS(POINT('ICRS', ra, dec), "
            f"CIRCLE('ICRS', {ra_deg}, {dec_deg}, {rad})) "
            f"ORDER BY dist ASC"
        )
        raw = self._fetch(adql)
        rows = _parse_csv(raw)
        if not rows:
            raise NotFoundError(
                f"Gaia cone vazio em {ra_deg:.5f},{dec_deg:.5f}"
            )
        return row_to_payload(rows[0], query=f"{ra_deg},{dec_deg}")

    def _fetch(self, adql: str) -> str:
        body = urlencode(
            {
                "REQUEST": "doQuery",
                "LANG": "ADQL",
                "FORMAT": "csv",
                "QUERY": adql,
            }
        ).encode("utf-8")
        if self._opener is not None:
            return self._opener(self.tap_url, body)
        req = Request(
            self.tap_url,
            data=body,
            headers={
                "User-Agent": "AstroCitizen/0.0.1 (GaiaTAP)",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )
        try:
            with urlopen(req, timeout=self.timeout_s) as resp:  # noqa: S310
                return resp.read().decode("utf-8", errors="replace")
        except HTTPError as exc:
            raise DomainError(f"Gaia TAP HTTP {exc.code}", rule_id="AC-213") from exc
        except URLError as exc:
            raise DomainError(
                f"Gaia TAP rede indisponivel: {exc.reason}", rule_id="AC-213"
            ) from exc
