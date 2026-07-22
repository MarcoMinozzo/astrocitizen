"""UI language resolution (RN-120): pt / es / en + auto + fallback en."""

from __future__ import annotations

import json
import locale as py_locale
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

SUPPORTED_LANGS = ("en", "pt", "es")
LangCode = str  # en | pt | es
PrefCode = str  # auto | en | pt | es

_LOCALES_DIR = Path(__file__).resolve().parent / "locales"
_current_lang: LangCode = "en"


def normalize_lang_tag(tag: str | None) -> LangCode | None:
    """Map BCP47 / POSIX tag to supported UI code, or None if unsupported."""
    if not tag:
        return None
    raw = tag.strip().replace("_", "-").lower()
    if not raw or raw in ("c", "posix"):
        return None
    primary = raw.split("-", 1)[0]
    if primary in SUPPORTED_LANGS:
        return primary
    return None


def detect_system_lang(
    *,
    environ: dict[str, str] | None = None,
    locale_name: str | None = None,
) -> str:
    """Best-effort system language tag (may be unsupported)."""
    env = environ if environ is not None else os.environ

    def _usable(val: str | None) -> str | None:
        if not val:
            return None
        first = val.split(":")[0].split(".")[0].strip()
        if not first or first.upper() in ("C", "POSIX"):
            return None
        return first

    for key in ("LC_ALL", "LC_MESSAGES", "LANGUAGE", "LANG"):
        found = _usable(env.get(key))
        if found:
            return found
    if locale_name is not None:
        found = _usable(locale_name)
        if found:
            return found
    try:
        name = py_locale.getlocale()[0] or py_locale.getdefaultlocale()[0]
    except Exception:  # noqa: BLE001
        name = None
    return _usable(name) or ""


def resolve_ui_lang(
    preference: PrefCode | None = "auto",
    *,
    detected: str | None = None,
) -> LangCode:
    """RN-120: explicit pref wins; auto uses detection; else en."""
    pref = (preference or "auto").strip().lower()
    if pref in SUPPORTED_LANGS:
        return pref
    # auto or unknown preference -> detect
    tag = detected if detected is not None else detect_system_lang()
    mapped = normalize_lang_tag(tag)
    return mapped if mapped else "en"


def set_current_lang(lang: LangCode) -> LangCode:
    global _current_lang
    mapped = normalize_lang_tag(lang) or "en"
    _current_lang = mapped
    return _current_lang


def get_current_lang() -> LangCode:
    return _current_lang


@lru_cache(maxsize=8)
def _load_catalog(lang: LangCode) -> dict[str, str]:
    path = _LOCALES_DIR / f"{lang}.json"
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}
    return {str(k): str(v) for k, v in data.items()}


def clear_catalog_cache() -> None:
    _load_catalog.cache_clear()


def t(key: str, lang: LangCode | None = None, **kwargs: Any) -> str:
    """Translate key; fallback lang -> en -> key itself."""
    code = normalize_lang_tag(lang) if lang else get_current_lang()
    code = code or "en"
    catalogs = (_load_catalog(code),)
    if code != "en":
        catalogs = (_load_catalog(code), _load_catalog("en"))
    text = None
    for cat in catalogs:
        if key in cat:
            text = cat[key]
            break
    if text is None:
        text = key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text


def help_topic_ids() -> list[str]:
    return [
        "getting_started",
        "night",
        "observatory",
        "program",
        "analyze",
        "contribute",
        "archive",
        "configure",
        "language",
    ]


def help_topic_title(topic_id: str, lang: LangCode | None = None) -> str:
    return t(f"help.{topic_id}.title", lang)


def help_topic_body(topic_id: str, lang: LangCode | None = None) -> str:
    return t(f"help.{topic_id}.body", lang)


def nav_area_label(area_key: str, lang: LangCode | None = None) -> str:
    return t(f"nav.{area_key}", lang)
