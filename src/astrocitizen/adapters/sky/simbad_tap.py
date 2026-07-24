"""SIMBAD TAP — coords + fotometria allfluxes (stdlib, sem astroquery)."""

from __future__ import annotations

import csv
import io
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from astrocitizen.shared.errors import DomainError, NotFoundError

_DEFAULT_TIMEOUT_S = 30.0
_TAP_SYNC = "https://simbad.cds.unistra.fr/simbad/sim-tap/sync"


def _sql_quote(ident: str) -> str:
    return "'" + ident.replace("'", "''") + "'"


def _parse_csv(raw: str) -> list[dict[str, str]]:
    text = (raw or "").strip()
    if not text or text.startswith("!!"):
        return []
    lines = text.splitlines()
    start = 0
    for i, ln in enumerate(lines):
        low = ln.lower()
        if "main_id" in low or ("," in ln and i > 0 and not ln.startswith("#")):
            # header often first non-comment data line
            if "main_id" in low or "otype" in low or "ra" in low:
                start = i
                break
    buf = io.StringIO("\n".join(lines[start:]))
    reader = csv.DictReader(buf)
    rows: list[dict[str, str]] = []
    for row in reader:
        if not row:
            continue
        # skip unit rows
        vals = [str(v or "").strip() for v in row.values()]
        if vals and all(v in ("", "deg", "mag", "Sun") or v.startswith("[") for v in vals):
            continue
        rows.append({k: (v or "").strip() for k, v in row.items() if k})
    return rows


def _f(row: dict[str, str], *keys: str) -> float | None:
    for k in keys:
        for rk, rv in row.items():
            if rk and rk.lower() == k.lower() and rv not in ("", "null", "None"):
                try:
                    return float(rv)
                except ValueError:
                    continue
    return None


def _s(row: dict[str, str], *keys: str) -> str | None:
    for k in keys:
        for rk, rv in row.items():
            if rk and rk.lower() == k.lower() and rv not in ("", "null", "None"):
                return str(rv).strip()
    return None


def row_to_payload(row: dict[str, str], *, query: str) -> dict[str, Any]:
    ra = _f(row, "ra")
    dec = _f(row, "dec")
    main_id = _s(row, "main_id") or query
    otype = _s(row, "otype_txt", "otype")
    vmag = _f(row, "V")
    bmag = _f(row, "B")
    rmag = _f(row, "R")
    imag = _f(row, "I")
    umag = _f(row, "U")
    gmag = _f(row, "G")  # SIMBAD G (não Gaia cone)

    external_ids: dict[str, Any] = {
        "simbad": main_id,
        "source": "simbad",
    }
    if otype:
        external_ids["otype"] = otype
    bands: list[str] = []
    if vmag is not None:
        external_ids["vmag"] = vmag
        bands.append(f"V={vmag}")
    if bmag is not None:
        external_ids["bmag"] = bmag
        bands.append(f"B={bmag}")
    if rmag is not None:
        external_ids["rmag"] = rmag
        bands.append(f"R={rmag}")
    if imag is not None:
        external_ids["imag"] = imag
        bands.append(f"I={imag}")
    if umag is not None:
        external_ids["umag"] = umag
        bands.append(f"U={umag}")
    if gmag is not None:
        # G SIMBAD (se existir) — distinto de gmag Gaia de cone
        external_ids["simbad_g"] = gmag
        bands.append(f"G={gmag}")

    # mag de referencia para agenda: preferir V, senao R, senao B
    ref = vmag if vmag is not None else (rmag if rmag is not None else bmag)
    if ref is not None and external_ids.get("mag_max") is None:
        # So preencher mag_max se nao houver VSX; o merge respeita VSX
        external_ids["mag_max"] = ref
    if bands:
        band_label = "SIMBAD " + ", ".join(bands)
        if vmag is None and ref is not None:
            which = "R" if rmag is not None and ref == rmag else "B"
            band_label += f" (ref {which}, sem V)"
        external_ids["band_notes"] = band_label

    out: dict[str, Any] = {
        "designation": main_id,
        "external_ids": external_ids,
    }
    if ra is not None and dec is not None:
        out["ra_deg"] = ra
        out["dec_deg"] = dec
    return out


class SimbadTapResolver:
    """Consulta SIMBAD TAP sync (CSV) por identificador."""

    def __init__(
        self,
        *,
        timeout_s: float = _DEFAULT_TIMEOUT_S,
        opener: Any | None = None,
        tap_url: str = _TAP_SYNC,
    ) -> None:
        self.timeout_s = timeout_s
        self._opener = opener
        self.tap_url = tap_url

    def resolve(self, name: str) -> dict[str, Any]:
        ident = (name or "").strip()
        if not ident:
            raise DomainError("nome SIMBAD vazio", rule_id="AC-236")
        q = _sql_quote(ident)
        # Tambem tentar "NGC 1200" se veio "NGC1200"
        alts = [ident]
        compact = ident.replace(" ", "")
        if compact != ident:
            alts.append(compact)
        spaced = _maybe_space_catalog(ident)
        if spaced and spaced not in alts:
            alts.append(spaced)

        quoted = ", ".join(_sql_quote(a) for a in alts)
        adql = f"""
SELECT TOP 1 b.main_id, b.otype_txt, b.ra, b.dec, f.U, f.B, f.V, f.R, f.I, f.G
FROM basic AS b
JOIN ident AS i ON i.oidref = b.oid
LEFT JOIN allfluxes AS f ON f.oidref = b.oid
WHERE i.id IN ({quoted})
""".strip()
        raw = self._fetch(adql)
        rows = _parse_csv(raw)
        if not rows:
            raise NotFoundError(f"SIMBAD TAP nao encontrou: {ident}")
        return row_to_payload(rows[0], query=ident)

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
                "User-Agent": "AstroCitizen/0.0.1 (SimbadTAP)",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )
        try:
            with urlopen(req, timeout=self.timeout_s) as resp:  # noqa: S310
                return resp.read().decode("utf-8", errors="replace")
        except HTTPError as exc:
            raise DomainError(f"SIMBAD TAP HTTP {exc.code}", rule_id="AC-236") from exc
        except URLError as exc:
            raise DomainError(
                f"SIMBAD TAP rede indisponivel: {exc.reason}", rule_id="AC-236"
            ) from exc


def _maybe_space_catalog(ident: str) -> str | None:
    """NGC1200 → NGC 1200; M56 → M 56."""
    import re

    m = re.match(r"^([A-Za-z]+)(\d+)$", ident.replace(" ", ""))
    if not m:
        return None
    return f"{m.group(1)} {m.group(2)}"
