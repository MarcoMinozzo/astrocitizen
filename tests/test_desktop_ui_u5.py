"""U5: series helpers + product detail (sem display)."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from astrocitizen.desktop.archive_panel import product_full_ids, product_rows
from astrocitizen.desktop.series import (
    cli_export_hint,
    export_networks_for_type,
    format_product_detail,
    primary_artifact_refs,
    resolve_openable_path,
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
        parameters={
            "fits_uri": "file:///tmp/a.fits",
            "noise": 1,
            "wcs_uri": "file:///w.fits",
        },
    )
    text = format_product_detail(p, n_points=100)
    assert "spectrum_1d" in text
    assert "points=100" in text
    assert "wave0_nm" in text
    assert "fits_uri" in text
    assert "wcs_uri" in text
    assert "noise" not in text  # only selected keys


def test_primary_artifact_refs_order() -> None:
    p = SimpleNamespace(
        parameters={
            "fits_uri": "file:///a.fits",
            "wcs_uri": "file:///w.fits",
            "noise": 1,
        }
    )
    refs = primary_artifact_refs(p)
    assert refs[0][0] == "wcs_uri"
    assert refs[1][0] == "fits_uri"


def test_resolve_openable_path_local(tmp_path: Path) -> None:
    f = tmp_path / "x.txt"
    f.write_text("ok", encoding="utf-8")
    assert resolve_openable_path(str(f)) == f.resolve()
    assert resolve_openable_path("file://" + str(f)) == f.resolve()
    assert resolve_openable_path("/no/such/file") is None


def test_resolve_under_store(tmp_path: Path) -> None:
    from astrocitizen.adapters.fs import LocalArtifactStore

    store = LocalArtifactStore(tmp_path)
    src = tmp_path / "in.bin"
    src.write_bytes(b"1")
    uri = store.put(src, key="analysis/gui/in.bin")
    path = resolve_openable_path(uri, store_root=tmp_path)
    assert path is not None and path.is_file()


def test_export_networks_and_cli_hint() -> None:
    assert export_networks_for_type("light_curve") == ["aavso", "exoclock"]
    assert export_networks_for_type("spectrum_1d") == ["bess"]
    assert export_networks_for_type("solar_sunspots") == ["solar"]
    tip = cli_export_hint("abcd", "light_curve")
    assert "aavso" in tip and "abcd" in tip


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
