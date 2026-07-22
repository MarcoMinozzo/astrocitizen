"""RN-120 i18n + smoke help/prefs builders."""

from __future__ import annotations

from astrocitizen.shared.i18n import (
    detect_system_lang,
    help_topic_body,
    help_topic_ids,
    normalize_lang_tag,
    resolve_ui_lang,
    set_current_lang,
    t,
)


def test_normalize_lang_tag() -> None:
    assert normalize_lang_tag("pt_BR") == "pt"
    assert normalize_lang_tag("pt-PT") == "pt"
    assert normalize_lang_tag("es_MX") == "es"
    assert normalize_lang_tag("en_US") == "en"
    assert normalize_lang_tag("de_DE") is None
    assert normalize_lang_tag("fr") is None
    assert normalize_lang_tag("") is None


def test_resolve_pref_overrides_system() -> None:
    assert resolve_ui_lang("es", detected="pt_BR") == "es"
    assert resolve_ui_lang("en", detected="pt_BR") == "en"
    assert resolve_ui_lang("pt", detected="de_DE") == "pt"


def test_resolve_auto_maps_and_fallback_en() -> None:
    assert resolve_ui_lang("auto", detected="pt_BR") == "pt"
    assert resolve_ui_lang("auto", detected="es_ES") == "es"
    assert resolve_ui_lang("auto", detected="de_DE") == "en"
    assert resolve_ui_lang("auto", detected="fr_FR") == "en"
    assert resolve_ui_lang("auto", detected="") == "en"
    assert resolve_ui_lang("bogus", detected="it_IT") == "en"


def test_detect_system_lang_from_environ() -> None:
    assert detect_system_lang(environ={"LANG": "pt_BR.UTF-8"}) == "pt_BR"
    assert detect_system_lang(environ={"LANGUAGE": "es:en", "LANG": "C"}) == "es"


def test_t_fallback_chain() -> None:
    set_current_lang("pt")
    assert t("nav.Noite") == "Noite"
    set_current_lang("es")
    assert t("nav.Noite") == "Noche"
    set_current_lang("en")
    assert t("nav.Noite") == "Night"
    assert t("missing.key.xyz") == "missing.key.xyz"
    assert "Getting started" in t("help.getting_started.title", lang="en")
    assert "Primeiros" in t("help.getting_started.title", lang="pt")


def test_help_topics_complete() -> None:
    ids = help_topic_ids()
    assert "getting_started" in ids
    assert "language" in ids
    for tid in ids:
        assert help_topic_body(tid, lang="en")
        assert help_topic_body(tid, lang="pt")
        assert help_topic_body(tid, lang="es")


def test_builders() -> None:
    from astrocitizen.desktop.help_panel import area_to_help_topic, build_help_panel
    from astrocitizen.desktop.prefs_panel import build_prefs_panel

    assert callable(build_help_panel)
    assert callable(build_prefs_panel)
    assert area_to_help_topic("Analisar") == "analyze"
    assert area_to_help_topic("Noite") == "night"


def test_ui_lang_pref_roundtrip_without_qt() -> None:
    # When Qt missing, load returns auto; save is no-op
    from astrocitizen.desktop import theme

    pref = theme.load_ui_lang_pref()
    assert pref in ("auto", "pt", "es", "en")
