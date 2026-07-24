"""AC-095: allowlist portal AAVSO + factory browser sem crash."""

from __future__ import annotations

import pytest

from astrocitizen.adapters.aavso_portal import (
    AAVSO_CAMPAIGNS_HOME,
    campaign_id_from_url,
    campaign_status_label,
    is_aavso_host,
)


def test_aavso_host_allowlist() -> None:
    assert is_aavso_host("https://apps.aavso.org/v2/campaigns/938")
    assert is_aavso_host("https://www.aavso.org/")
    assert is_aavso_host("https://aavso.org/apis-aavso-resources")
    assert not is_aavso_host("https://evil.example/aavso.org")
    assert not is_aavso_host("https://notaavso.org/")
    assert not is_aavso_host("not-a-url")


def test_campaign_id_from_url() -> None:
    assert campaign_id_from_url("https://apps.aavso.org/v2/campaigns/938") == "938"
    assert campaign_id_from_url("https://apps.aavso.org/v2/campaigns/938/") == "938"
    assert campaign_id_from_url(AAVSO_CAMPAIGNS_HOME) is None
    assert campaign_id_from_url("https://apps.aavso.org/v2/campaigns/search") is None


def test_campaign_status_label() -> None:
    assert campaign_status_label("https://apps.aavso.org/v2/campaigns/938") == (
        "Campanha 938"
    )
    assert campaign_status_label(AAVSO_CAMPAIGNS_HOME) == "AAVSO"
    assert campaign_status_label("https://example.com") == ""


def test_browser_factory_is_callable() -> None:
    from astrocitizen.desktop.aavso_campaigns_browser import (
        build_aavso_campaigns_browser,
        webengine_available,
    )

    assert callable(build_aavso_campaigns_browser)
    assert isinstance(webengine_available(), bool)


def test_webengine_opt_in_default_off(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from astrocitizen.desktop import aavso_campaigns_browser as mod

    monkeypatch.delenv("ASTROCITIZEN_WEBENGINE", raising=False)
    monkeypatch.delenv("ASTROCITIZEN_NO_WEBENGINE", raising=False)
    assert mod.webengine_available() is False
    monkeypatch.setenv("ASTROCITIZEN_WEBENGINE", "1")

    def _ok() -> None:
        return None

    monkeypatch.setattr(
        mod,
        "webengine_available",
        mod.webengine_available,
    )
    # Com flag=1, depende de QtWebEngine instalado — so garantir que nao e sempre True
    # sem o pacote: se ImportError, False.
    try:
        from PySide6.QtWebEngineWidgets import QWebEngineView  # noqa: F401

        assert mod.webengine_available() is True
    except ImportError:
        assert mod.webengine_available() is False


def test_browser_fallback_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sem WebEngine, o painel usa fallback (sem crash)."""
    pytest.importorskip("PySide6")
    import os

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    import astrocitizen.desktop.aavso_campaigns_browser as mod

    monkeypatch.setattr(mod, "webengine_available", lambda: False)
    app = QApplication.instance() or QApplication([])
    Browser = mod.build_aavso_campaigns_browser()
    w = Browser()
    assert w._view is None
    assert w._home == AAVSO_CAMPAIGNS_HOME
    w.close()
    _ = app
