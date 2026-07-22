"""U0/U1: widgets partilhados + IA 6 areas."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

from astrocitizen.desktop.app import NAV_AREA_KEYS
from astrocitizen.desktop.theme import app_stylesheet
from astrocitizen.desktop.widgets import refill_program_combo, refill_site_combo


class _FakeCombo:
    def __init__(self) -> None:
        self.items: list[tuple[str, object]] = []
        self._index = 0

    def clear(self) -> None:
        self.items = []
        self._index = 0

    def addItem(self, label: str, data: object = None) -> None:
        self.items.append((label, data))

    def findData(self, data: object) -> int:
        for i, (_, d) in enumerate(self.items):
            if d == data:
                return i
        return -1

    def setCurrentIndex(self, i: int) -> None:
        self._index = i


def test_nav_six_areas() -> None:
    assert len(NAV_AREA_KEYS) == 6
    assert NAV_AREA_KEYS[0] == "Noite"
    assert NAV_AREA_KEYS[1] == "Observatorio"
    assert "Analisar" in NAV_AREA_KEYS
    assert "Configurar" in NAV_AREA_KEYS
    assert "Import" not in NAV_AREA_KEYS
    assert "Radio" not in NAV_AREA_KEYS


def test_theme_has_context_bar() -> None:
    css = app_stylesheet()
    assert "contextBar" in css
    assert "brandBar" in css


def test_refill_site_combo() -> None:
    combo = _FakeCombo()
    sid = uuid4()
    sites = [SimpleNamespace(id=sid, name="Casa")]
    refill_site_combo(combo, sites, current=sid)
    assert combo.items[0] == ("(nenhum)", None)
    assert combo.items[1][0] == "Casa"
    assert combo._index == 1


def test_refill_program_combo() -> None:
    combo = _FakeCombo()
    pid = uuid4()
    progs = [SimpleNamespace(id=pid, template_id="PO-A01", name="Vars")]
    refill_program_combo(combo, progs, current=pid)
    assert "PO-A01" in combo.items[1][0]
    assert combo._index == 1


def test_build_shared_widgets_callable() -> None:
    from astrocitizen.desktop.widgets import build_shared_widgets

    assert callable(build_shared_widgets)
