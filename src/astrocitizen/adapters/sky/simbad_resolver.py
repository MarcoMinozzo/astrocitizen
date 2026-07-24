"""Resolver SIMBAD — TAP (fotometria) com fallback astroquery."""

from __future__ import annotations

from typing import Any

from astrocitizen.adapters.sky.simbad_tap import SimbadTapResolver
from astrocitizen.shared.errors import DomainError, NotFoundError


class SimbadResolver:
    """TargetResolverPort: preferir TAP (coords+fluxos); fallback astroquery."""

    def __init__(
        self,
        *,
        tap: SimbadTapResolver | None = None,
        prefer_tap: bool = True,
    ) -> None:
        self._tap = tap or SimbadTapResolver()
        self._prefer_tap = prefer_tap

    def resolve(self, name: str) -> dict[str, Any]:
        if self._prefer_tap:
            try:
                return self._tap.resolve(name)
            except (NotFoundError, DomainError):
                pass
        return self._resolve_astroquery(name)

    def _resolve_astroquery(self, name: str) -> dict[str, Any]:
        try:
            from astroquery.simbad import Simbad
        except ImportError as exc:
            raise DomainError(
                "astroquery nao instalado e SIMBAD TAP falhou; "
                "use `pip install astrocitizen[sky]` ou forneca --ra/--dec",
                rule_id="AC-031",
            ) from exc

        result = Simbad.query_object(name)
        if result is None or len(result) == 0:
            raise NotFoundError(f"SIMBAD nao encontrou: {name}")

        row = result[0]
        ra = None
        dec = None
        for ra_key in ("ra", "RA", "RA_d"):
            if ra_key in result.colnames:
                ra = float(row[ra_key])
                break
        for dec_key in ("dec", "DEC", "DEC_d"):
            if dec_key in result.colnames:
                dec = float(row[dec_key])
                break
        if ra is None or dec is None:
            import astropy.units as u
            from astropy.coordinates import SkyCoord

            ra_str = str(row["ra"] if "ra" in result.colnames else row["RA"])
            dec_str = str(row["dec"] if "dec" in result.colnames else row["DEC"])
            coord = SkyCoord(f"{ra_str} {dec_str}", unit=(u.hourangle, u.deg), frame="icrs")
            ra = float(coord.ra.deg)
            dec = float(coord.dec.deg)

        return {
            "ra_deg": ra,
            "dec_deg": dec,
            "designation": name,
            "external_ids": {"simbad": name, "source": "simbad"},
        }
