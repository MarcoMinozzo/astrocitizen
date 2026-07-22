"""Testes do tema e helpers UX do shell."""

from __future__ import annotations

from astrocitizen.desktop.theme import (
    COLORS,
    NIGHT_VISION_COLORS,
    app_stylesheet,
    empty_state_text,
    palette_for,
    viability_badge,
)


def test_theme_stylesheet_tokens() -> None:
    css = app_stylesheet()
    assert COLORS["accent"] in css
    assert COLORS["bg"] in css
    assert "navList" in css
    assert "badgeOk" in css
    assert "nightVisionBtn" in css
    assert "purple" not in css.lower()


def test_night_vision_stylesheet() -> None:
    css = app_stylesheet(night_vision=True)
    assert NIGHT_VISION_COLORS["bg"] in css
    assert NIGHT_VISION_COLORS["accent"] in css
    assert COLORS["bg"] not in css
    # Sem azuis claros / ambar do tema ops
    assert COLORS["accent"] not in css


def test_palette_for() -> None:
    assert palette_for(night_vision=False)["accent"] == COLORS["accent"]
    assert palette_for(night_vision=True)["accent"] == NIGHT_VISION_COLORS["accent"]
    # Vermelho dominante (canal R > G e R > B nos hex principais)
    nv = NIGHT_VISION_COLORS
    for key in ("bg", "text", "accent", "border"):
        h = nv[key].lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        assert r >= g and r >= b


def test_viability_badge() -> None:
    assert viability_badge(True) == ("VIABLE", "badgeOk")
    assert viability_badge(False) == ("INVIABLE", "badgeBad")
    assert viability_badge(None)[1] == "badgeIdle"


def test_empty_state_text() -> None:
    assert "site add" in empty_state_text("Sites")
    assert "Gerar plano" in empty_state_text("Plano diario")
    assert empty_state_text("Outro") == "Sem dados."
