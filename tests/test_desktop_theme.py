"""Testes do tema e helpers UX do shell."""

from __future__ import annotations

from astrocitizen.desktop.theme import (
    COLORS,
    app_stylesheet,
    empty_state_text,
    viability_badge,
)


def test_theme_stylesheet_tokens() -> None:
    css = app_stylesheet()
    assert COLORS["accent"] in css
    assert COLORS["bg"] in css
    assert "navList" in css
    assert "badgeOk" in css
    assert "purple" not in css.lower()


def test_viability_badge() -> None:
    assert viability_badge(True) == ("VIABLE", "badgeOk")
    assert viability_badge(False) == ("INVIABLE", "badgeBad")
    assert viability_badge(None)[1] == "badgeIdle"


def test_empty_state_text() -> None:
    assert "site add" in empty_state_text("Sites")
    assert "Gerar plano" in empty_state_text("Plano diario")
    assert empty_state_text("Outro") == "Sem dados."
