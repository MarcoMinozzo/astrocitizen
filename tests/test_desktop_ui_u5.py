"""U5: series helpers + product detail (sem display)."""

from __future__ import annotations

from types import SimpleNamespace

from astrocitizen.desktop.archive_panel import product_full_ids, product_rows
from astrocitizen.desktop.series import (
    format_product_detail,
    series_from_measurement_points,
)


def test_series_from_measurement_points_prefers_xy() -> None:
    xs, ys, band = series_from_measurement_points(
        [
            {"x": 10.0, "y": 1.5, "band": "R"},
            {"x": 11.0, "y": 1.2},
            {"y": None},
            {"sequence_index": 99, "y": 0.9},
        ]
    )
    assert xs == [10.0, 11.0, 99.0]
    assert ys == [1.5, 1.2, 0.9]
    assert band == "R"


def test_series_skips_bad_y() -> None:
    xs, ys, band = series_from_measurement_points(
        [{"x": 1, "y": "bad"}, {"x": 2, "y": 3}]
    )
    assert xs == [2.0]
    assert ys == [3.0]
    assert band == "y"


def test_format_product_detail() -> None:
    p = SimpleNamespace(
        id="11111111-1111-1111-1111-111111111111",
        product_type="spectrum_1d",
        state="ready",
        summary={"n_points": 100, "wave0_nm": 400},
        parameters={"fits_uri": "file:///tmp/a.fits", "noise": 1},
    )
    text = format_product_detail(p, n_points=100)
    assert "spectrum_1d" in text
    assert "points=100" in text
    assert "wave0_nm" in text
    assert "fits_uri" in text
    assert "noise" not in text  # only selected keys


def test_product_full_ids_align_with_rows() -> None:
    products = [
        SimpleNamespace(
            id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            product_type="lc",
            state="ok",
            summary={},
        ),
        SimpleNamespace(
            id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            product_type="sp",
            state="ok",
            summary={"a": 1},
        ),
    ]
    rows = product_rows(products)
    ids = product_full_ids(products)
    assert len(rows) == len(ids) == 2
    assert rows[0][3] == ids[0][:8]
    assert ids[1].startswith("bbbbbbbb")
