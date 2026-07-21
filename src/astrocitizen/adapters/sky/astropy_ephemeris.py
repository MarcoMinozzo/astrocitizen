"""Adapter EphemerisPort com Astropy."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from astropy import units as u
from astropy.coordinates import AltAz, EarthLocation, SkyCoord, get_body
from astropy.time import Time

from astrocitizen.shared.errors import DomainError


def _parse_utc(utc_iso: str) -> Time:
    text = utc_iso.replace("Z", "+00:00")
    return Time(datetime.fromisoformat(text), scale="utc")


def _iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class AstropyEphemeris:
    """Efemerides locais AltAz + janela de noite (crepusculo astronomico)."""

    def altitude_azimuth(
        self,
        *,
        ra_deg: float,
        dec_deg: float,
        latitude_deg: float,
        longitude_deg: float,
        elevation_m: float,
        utc_iso: str,
    ) -> dict[str, float | None]:
        loc = EarthLocation(
            lat=latitude_deg * u.deg,
            lon=longitude_deg * u.deg,
            height=elevation_m * u.m,
        )
        t = _parse_utc(utc_iso)
        frame = AltAz(obstime=t, location=loc)
        coord = SkyCoord(ra=ra_deg * u.deg, dec=dec_deg * u.deg, frame="icrs")
        altaz = coord.transform_to(frame)
        alt = float(altaz.alt.deg)
        az = float(altaz.az.deg)
        airmass: float | None
        if alt <= 0:
            airmass = None
        else:
            airmass = float(altaz.secz) if alt > 5 else None
            if airmass is not None and (airmass < 1 or airmass > 40):
                airmass = None
        return {"alt_deg": alt, "az_deg": az, "airmass": airmass}

    def night_window(
        self,
        *,
        latitude_deg: float,
        longitude_deg: float,
        elevation_m: float,
        night_date: str,
        night_start_rule: str = "astronomical_twilight",
    ) -> dict[str, str]:
        """Aproxima noite: Sol abaixo do limiar (default -18 deg) apos o dia night_date.

        night_date = data civil do inicio da noite no site (YYYY-MM-DD).
        """
        if night_start_rule not in (
            "astronomical_twilight",
            "nautical_twilight",
            "civil_twilight",
            "sunset",
        ):
            raise DomainError(f"night_start_rule desconhecida: {night_start_rule}")

        sun_alt_limit = {
            "astronomical_twilight": -18.0,
            "nautical_twilight": -12.0,
            "civil_twilight": -6.0,
            "sunset": -0.833,
        }[night_start_rule]

        loc = EarthLocation(
            lat=latitude_deg * u.deg,
            lon=longitude_deg * u.deg,
            height=elevation_m * u.m,
        )
        # Sample from ~noon UTC of night_date for 30h (20-min steps — D-010)
        day = datetime.fromisoformat(night_date).replace(tzinfo=timezone.utc)
        start_sample = day + timedelta(hours=12)
        step = timedelta(minutes=20)
        n_steps = int(30 * 60 / 20)
        times = [start_sample + i * step for i in range(n_steps)]
        alts: list[tuple[datetime, float]] = []
        for dt in times:
            t = Time(dt)
            sun = get_body("sun", t, location=loc)
            altaz = sun.transform_to(AltAz(obstime=t, location=loc))
            alts.append((dt, float(altaz.alt.deg)))

        night_start: datetime | None = None
        night_end: datetime | None = None
        for i in range(1, len(alts)):
            prev_t, prev_a = alts[i - 1]
            cur_t, cur_a = alts[i]
            if night_start is None and prev_a >= sun_alt_limit and cur_a < sun_alt_limit:
                night_start = cur_t
            if night_start is not None and night_end is None and prev_a < sun_alt_limit and cur_a >= sun_alt_limit:
                night_end = cur_t
                break

        if night_start is None or night_end is None:
            # Fallback: 22:00 UTC to 06:00 UTC next day
            night_start = day + timedelta(hours=22)
            night_end = day + timedelta(days=1, hours=6)

        return {"start_utc": _iso_z(night_start), "end_utc": _iso_z(night_end)}
