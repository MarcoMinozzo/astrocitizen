"""AC-038 / AC-079: projecao zenith + modelo carta do plano."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

from astrocitizen.adapters.sky import AstropyEphemeris
from astrocitizen.planning.sky_projection import (
    altaz_to_sky_xy,
    altitude_to_radius,
    build_sky_chart_model,
    classify_target_state,
    interpolate_night_utc,
    night_fraction_for_utc,
)


def test_altaz_zenith_is_center() -> None:
    xy = altaz_to_sky_xy(90.0, 0.0)
    assert xy is not None
    assert abs(xy[0]) < 1e-9 and abs(xy[1]) < 1e-9


def test_altaz_horizon_north() -> None:
    xy = altaz_to_sky_xy(0.0, 0.0)
    assert xy is not None
    assert abs(xy[0]) < 1e-9
    assert abs(xy[1] - 1.0) < 1e-9


def test_altaz_horizon_east() -> None:
    xy = altaz_to_sky_xy(0.0, 90.0)
    assert xy is not None
    assert abs(xy[0] - 1.0) < 1e-9
    assert abs(xy[1]) < 1e-9


def test_altaz_below_horizon() -> None:
    assert altaz_to_sky_xy(-5.0, 10.0) is None
    xy = altaz_to_sky_xy(-5.0, 90.0, clamp_horizon=True)
    assert xy is not None
    assert abs(xy[0] - 1.0) < 1e-9


def test_min_alt_radius() -> None:
    assert abs(altitude_to_radius(25.0) - (65.0 / 90.0)) < 1e-9


def test_classify_states() -> None:
    assert classify_target_state(40.0, min_altitude_deg=25.0) == "above"
    assert classify_target_state(10.0, min_altitude_deg=25.0) == "below_threshold"
    assert classify_target_state(-1.0) == "below_horizon"
    assert (
        classify_target_state(50.0, block_status="inviavel_ceu") == "inviavel_ceu"
    )


def test_night_fraction_roundtrip() -> None:
    start = "2026-07-21T22:00:00Z"
    end = "2026-07-22T06:00:00Z"
    mid = interpolate_night_utc(start, end, 0.5)
    assert night_fraction_for_utc(start, end, mid) == 0.5


def test_build_model_with_target_and_bodies() -> None:
    eph = AstropyEphemeris()
    site = SimpleNamespace(
        name="Casa",
        latitude_deg=-29.7,
        longitude_deg=-51.1,
        elevation_m=100.0,
        min_altitude_deg=25.0,
    )
    tid = uuid4()
    bid = uuid4()
    target = SimpleNamespace(id=tid, designation="Vega", ra_deg=279.23, dec_deg=38.78)
    block = SimpleNamespace(id=bid, target_id=tid, status="agendado")
    model = build_sky_chart_model(
        ephemeris=eph,
        site=site,
        utc_iso="2026-07-22T02:00:00Z",
        blocks=[block],
        targets_by_id={tid: target},
        include_sun_moon=True,
    )
    assert model.site_name == "Casa"
    kinds = {m.kind for m in model.markers}
    assert "target" in kinds
    assert "sun" in kinds
    assert "moon" in kinds
    vega = next(m for m in model.markers if m.kind == "target")
    assert vega.label == "Vega"
    assert vega.block_id == bid


def test_southern_site_projection_stable() -> None:
    """Hemisferio sul: projecao nao explode; azimute norte continua +y."""
    xy = altaz_to_sky_xy(45.0, 0.0)
    assert xy is not None
    assert xy[1] > 0
    assert abs(xy[0]) < 1e-9
