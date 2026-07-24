"""Loaders de form_schema.json por rede (D-013 / AC-220)."""

from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Any

from astrocitizen.shared.errors import NotFoundError

_PACKAGE_ROOT = "astrocitizen.integrations"


def form_schema_path(network: str) -> Path | None:
    """Path no filesystem se o pacote estiver expandido; senao None."""
    key = (network or "").strip().lower()
    try:
        base = resources.files(_PACKAGE_ROOT)
        candidate = base.joinpath(key, "form_schema.json")
        with resources.as_file(candidate) as p:
            if p.is_file():
                return Path(p)
    except (FileNotFoundError, ModuleNotFoundError, TypeError, AttributeError):
        pass
    # Dev fallback: relative to this file's integrations tree
    here = Path(__file__).resolve().parent
    p2 = here / key / "form_schema.json"
    return p2 if p2.is_file() else None


@lru_cache(maxsize=32)
def load_form_schema(network: str) -> dict[str, Any]:
    """Carrega schema de formulario atlas-compativel."""
    key = (network or "").strip().lower()
    if not key:
        raise NotFoundError("network vazio")
    try:
        text = (
            resources.files(_PACKAGE_ROOT)
            .joinpath(key, "form_schema.json")
            .read_text(encoding="utf-8")
        )
    except (FileNotFoundError, ModuleNotFoundError, OSError, AttributeError) as exc:
        path = form_schema_path(key)
        if path is None:
            raise NotFoundError(f"form_schema nao encontrado: {key}") from exc
        text = path.read_text(encoding="utf-8")
    data = json.loads(text)
    if not isinstance(data, dict) or data.get("network") != key:
        raise NotFoundError(f"form_schema invalido para {key}")
    return data


def list_form_networks() -> list[str]:
    """Redes com form_schema.json empacotado."""
    found: list[str] = []
    try:
        root = resources.files(_PACKAGE_ROOT)
        for child in root.iterdir():
            if child.is_dir() and (child / "form_schema.json").is_file():
                found.append(child.name)
    except (FileNotFoundError, ModuleNotFoundError, AttributeError, TypeError):
        here = Path(__file__).resolve().parent
        for child in here.iterdir():
            if child.is_dir() and (child / "form_schema.json").is_file():
                found.append(child.name)
    return sorted(found)
