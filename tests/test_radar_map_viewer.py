"""Testes do mapa radar Leaflet/RainViewer (sem GUI)."""

from __future__ import annotations

from pathlib import Path

from astrocitizen.desktop.radar_map_html import build_radar_map_html, write_radar_map_html


def test_build_radar_map_html_centers_site() -> None:
    html = build_radar_map_html(
        latitude_deg=-29.6842,
        longitude_deg=-51.1321,
        zoom=7,
        site_name='Observatorio Casa <X>',
    )
    assert "CENTER_LAT = -29.6842" in html
    assert "CENTER_LON = -51.1321" in html
    assert "START_ZOOM = 7" in html
    assert "Observatorio Casa &lt;X&gt;" in html
    assert "api.rainviewer.com" in html
    assert "leaflet" in html.lower()
    assert "OpenStreetMap" in html


def test_write_radar_map_html(tmp_path: Path) -> None:
    out = write_radar_map_html(
        tmp_path / "radar.html",
        latitude_deg=10.5,
        longitude_deg=-60.25,
        site_name="Site",
    )
    assert out.is_file()
    text = out.read_text(encoding="utf-8")
    assert "CENTER_LAT = 10.5" in text
    assert "CENTER_LON = -60.25" in text
