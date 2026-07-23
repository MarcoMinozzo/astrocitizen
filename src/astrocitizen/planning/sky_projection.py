"""Projecao AltAz -> carta zenith (AC-038) + modelo de marcadores (AC-079).

Carta operacional L0: zenith no centro, horizonte no bordo, Norte para cima,
Este para a direita. Sem catalogo estelar.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from uuid import UUID

SkyMarkerKind = Literal["target", "sun", "moon", "star"]
SkyVisualState = Literal[
    "above",
    "below_threshold",
    "below_horizon",
    "inviavel_ceu",
    "body",
    "star",
]

DEFAULT_MIN_ALTITUDE_DEG = 25.0


@dataclass(slots=True)
class SkyMarker:
    """Ponto na carta (coords normalizadas x,y em [-1,1] se acima do horizonte)."""

    kind: SkyMarkerKind
    label: str
    alt_deg: float
    az_deg: float
    state: SkyVisualState
    x: float | None
    y: float | None
    block_id: UUID | None = None
    target_id: UUID | None = None
    status: str | None = None


@dataclass(slots=True)
class SkyChartModel:
    utc_iso: str
    min_altitude_deg: float
    markers: list[SkyMarker]
    night_start_utc: str | None = None
    night_end_utc: str | None = None
    site_name: str = ""

    @property
    def min_alt_radius(self) -> float:
        """Raio normalizado do circulo de altitude minima (0=zenith, 1=horizonte)."""
        return altitude_to_radius(self.min_altitude_deg)

    @property
    def n_stars(self) -> int:
        return sum(1 for m in self.markers if m.kind == "star")

    @property
    def status_line(self) -> str:
        n = self.n_targets
        ns = self.n_stars
        bits = []
        if ns:
            bits.append(f"{ns} estrela(s) brilhantes")
        if n == 0:
            bits.append("sem alvos do plano (Gerar plano)")
        else:
            bits.append(f"{n} alvo(s) do plano")
        bits.append("↓ = abaixo do horizonte")
        return " · ".join(bits)


def altitude_to_radius(alt_deg: float) -> float:
    """Mapa linear: zenith (90) -> 0, horizonte (0) -> 1."""
    return max(0.0, min(1.0, (90.0 - float(alt_deg)) / 90.0))


def altaz_to_sky_xy(
    alt_deg: float, az_deg: float, *, clamp_horizon: bool = False
) -> tuple[float, float] | None:
    """Projecao azimutal equidistante centrada no zenith.

    Norte = +y, Este = +x. Devolve None se abaixo do horizonte (alt < 0),
    salvo `clamp_horizon=True` (projecta no bordo do horizonte).
    """
    alt = float(alt_deg)
    if alt < 0.0:
        if not clamp_horizon:
            return None
        alt = 0.0
    r = altitude_to_radius(alt)
    az = math.radians(float(az_deg) % 360.0)
    x = r * math.sin(az)
    y = r * math.cos(az)
    return (x, y)


def classify_target_state(
    alt_deg: float,
    *,
    min_altitude_deg: float = DEFAULT_MIN_ALTITUDE_DEG,
    block_status: str | None = None,
) -> SkyVisualState:
    if block_status == "inviavel_ceu":
        return "inviavel_ceu"
    if alt_deg < 0.0:
        return "below_horizon"
    if alt_deg < float(min_altitude_deg):
        return "below_threshold"
    return "above"


def parse_utc_iso(utc_iso: str) -> datetime:
    text = utc_iso.replace("Z", "+00:00")
    return datetime.fromisoformat(text).astimezone(timezone.utc)


def iso_z(dt: datetime) -> str:
    return (
        dt.astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def interpolate_night_utc(
    night_start_utc: str,
    night_end_utc: str,
    fraction: float,
) -> str:
    """fraction in [0, 1] ao longo da janela da noite."""
    t0 = parse_utc_iso(night_start_utc)
    t1 = parse_utc_iso(night_end_utc)
    f = max(0.0, min(1.0, float(fraction)))
    return iso_z(t0 + (t1 - t0) * f)


def night_fraction_for_utc(
    night_start_utc: str,
    night_end_utc: str,
    utc_iso: str,
) -> float:
    t0 = parse_utc_iso(night_start_utc)
    t1 = parse_utc_iso(night_end_utc)
    t = parse_utc_iso(utc_iso)
    span = (t1 - t0).total_seconds()
    if span <= 0:
        return 0.0
    return max(0.0, min(1.0, (t - t0).total_seconds() / span))


def make_marker(
    *,
    kind: SkyMarkerKind,
    label: str,
    alt_deg: float,
    az_deg: float,
    state: SkyVisualState,
    block_id: UUID | None = None,
    target_id: UUID | None = None,
    status: str | None = None,
) -> SkyMarker:
    # Sempre projectar (abaixo do horizonte → bordo) para Sol/Lua/alvos serem visiveis.
    xy = altaz_to_sky_xy(alt_deg, az_deg, clamp_horizon=True)
    assert xy is not None
    display = label
    if alt_deg < 0.0 and kind in ("sun", "moon", "target"):
        display = f"{label} ↓"
    return SkyMarker(
        kind=kind,
        label=display,
        alt_deg=alt_deg,
        az_deg=az_deg,
        state=state,
        x=xy[0],
        y=xy[1],
        block_id=block_id,
        target_id=target_id,
        status=status,
    )


def build_sky_chart_model(
    *,
    ephemeris: Any,
    site: Any,
    utc_iso: str,
    blocks: list[Any] | None = None,
    targets_by_id: dict[UUID, Any] | None = None,
    min_altitude_deg: float | None = None,
    night_start_utc: str | None = None,
    night_end_utc: str | None = None,
    include_sun_moon: bool = True,
    include_bright_stars: bool = True,
    star_max_vmag: float = 2.2,
) -> SkyChartModel:
    """Monta marcadores: estrelas brilhantes + alvos do plano + Sol/Lua."""
    min_alt = float(
        min_altitude_deg
        if min_altitude_deg is not None
        else getattr(site, "min_altitude_deg", DEFAULT_MIN_ALTITUDE_DEG)
    )
    lat = float(site.latitude_deg)
    lon = float(site.longitude_deg)
    elev = float(getattr(site, "elevation_m", 0.0) or 0.0)
    markers: list[SkyMarker] = []
    targets_by_id = targets_by_id or {}

    if include_bright_stars:
        from astrocitizen.planning.bright_stars import stars_brighter_than

        for star in stars_brighter_than(star_max_vmag):
            aa = ephemeris.altitude_azimuth(
                ra_deg=star.ra_deg,
                dec_deg=star.dec_deg,
                latitude_deg=lat,
                longitude_deg=lon,
                elevation_m=elev,
                utc_iso=utc_iso,
            )
            alt = float(aa["alt_deg"])
            if alt < 0.0:
                continue  # so estrelas acima do horizonte
            az = float(aa["az_deg"])
            markers.append(
                make_marker(
                    kind="star",
                    label=star.name if star.vmag <= 1.0 else "",
                    alt_deg=alt,
                    az_deg=az,
                    state="star",
                    status=f"V={star.vmag:.2f}",
                )
            )

    for block in blocks or []:
        tid = getattr(block, "target_id", None)
        if tid is None:
            continue
        target = targets_by_id.get(tid)
        if target is None:
            continue
        ra = getattr(target, "ra_deg", None)
        dec = getattr(target, "dec_deg", None)
        if ra is None or dec is None:
            continue
        aa = ephemeris.altitude_azimuth(
            ra_deg=float(ra),
            dec_deg=float(dec),
            latitude_deg=lat,
            longitude_deg=lon,
            elevation_m=elev,
            utc_iso=utc_iso,
        )
        alt = float(aa["alt_deg"])
        az = float(aa["az_deg"])
        status = getattr(block, "status", None)
        state = classify_target_state(
            alt, min_altitude_deg=min_alt, block_status=status
        )
        label = getattr(target, "designation", None) or str(tid)[:8]
        markers.append(
            make_marker(
                kind="target",
                label=str(label),
                alt_deg=alt,
                az_deg=az,
                state=state,
                block_id=getattr(block, "id", None),
                target_id=tid,
                status=status,
            )
        )

    if include_sun_moon and hasattr(ephemeris, "body_altitude_azimuth"):
        for body, kind, label in (
            ("sun", "sun", "Sol"),
            ("moon", "moon", "Lua"),
        ):
            aa = ephemeris.body_altitude_azimuth(
                body=body,
                latitude_deg=lat,
                longitude_deg=lon,
                elevation_m=elev,
                utc_iso=utc_iso,
            )
            alt = float(aa["alt_deg"])
            az = float(aa["az_deg"])
            markers.append(
                make_marker(
                    kind=kind,  # type: ignore[arg-type]
                    label=label,
                    alt_deg=alt,
                    az_deg=az,
                    state="below_horizon" if alt < 0 else "body",
                )
            )

    return SkyChartModel(
        utc_iso=utc_iso,
        min_altitude_deg=min_alt,
        markers=markers,
        night_start_utc=night_start_utc,
        night_end_utc=night_end_utc,
        site_name=str(getattr(site, "name", "") or ""),
    )


def load_sky_chart_from_archive(
    archive: Any,
    *,
    workspace_id: UUID,
    site: Any,
    night_date: str,
    utc_iso: str,
    ephemeris: Any,
    night_window: dict[str, str] | None = None,
    include_bright_stars: bool = True,
) -> SkyChartModel:
    """Carrega plano do arquivo e constroi o modelo da carta."""
    plan = archive.get_daily_plan_for_night(workspace_id, site.id, night_date)
    blocks = archive.list_observation_blocks(plan.id) if plan is not None else []
    targets: dict[UUID, Any] = {}
    for b in blocks:
        if b.target_id is None:
            continue
        t = archive.get_target(b.target_id)
        if t is not None:
            targets[b.target_id] = t
    nw = night_window
    if nw is None and hasattr(ephemeris, "night_window"):
        nw = ephemeris.night_window(
            latitude_deg=site.latitude_deg,
            longitude_deg=site.longitude_deg,
            elevation_m=site.elevation_m,
            night_date=night_date,
            night_start_rule=getattr(site, "night_start_rule", "astronomical_twilight"),
        )
    return build_sky_chart_model(
        ephemeris=ephemeris,
        site=site,
        utc_iso=utc_iso,
        blocks=blocks,
        targets_by_id=targets,
        night_start_utc=(nw or {}).get("start_utc"),
        night_end_utc=(nw or {}).get("end_utc"),
        include_bright_stars=include_bright_stars,
    )


def clamp_utc_to_night(
    utc_iso: str,
    night_start_utc: str,
    night_end_utc: str,
) -> str:
    t = parse_utc_iso(utc_iso)
    t0 = parse_utc_iso(night_start_utc)
    t1 = parse_utc_iso(night_end_utc)
    if t < t0:
        return night_start_utc
    if t > t1:
        return night_end_utc
    return iso_z(t)


def now_utc_iso() -> str:
    return iso_z(datetime.now(timezone.utc))


def add_hours_iso(utc_iso: str, hours: float) -> str:
    return iso_z(parse_utc_iso(utc_iso) + timedelta(hours=hours))
