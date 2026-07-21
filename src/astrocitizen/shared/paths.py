"""Resolucao de caminhos de dados locais (Desktop)."""

from __future__ import annotations

import os
from pathlib import Path


def default_data_dir() -> Path:
    override = os.environ.get("ASTROCITIZEN_DATA")
    if override:
        return Path(override).expanduser().resolve()
    return (Path.home() / ".astrocitizen").resolve()


def default_db_path() -> Path:
    return default_data_dir() / "astrocitizen.sqlite3"


def default_artifacts_root() -> Path:
    return default_data_dir() / "artifacts"
