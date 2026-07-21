"""Seed do catálogo de templates PO-*."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path

from astrocitizen.programs.models import ProgramTemplate


def load_program_templates_json(path: Path | None = None) -> list[dict]:
    if path is not None:
        return json.loads(path.read_text(encoding="utf-8"))
    pkg = resources.files("astrocitizen.programs")
    data = pkg.joinpath("catalog/program_templates.json")
    return json.loads(data.read_text(encoding="utf-8"))


def templates_from_records(records: list[dict]) -> list[ProgramTemplate]:
    out: list[ProgramTemplate] = []
    for r in records:
        out.append(
            ProgramTemplate(
                id=r["id"],
                class_=r["class"],
                name=r["name"],
                technique=r.get("technique", ""),
                default_networks=list(r.get("default_networks") or []),
                minimum_product=r.get("minimum_product", ""),
                priority=r.get("priority", "P3"),
                metadata=dict(r.get("metadata") or {}),
            )
        )
    return out


def seed_program_templates(archive, path: Path | None = None) -> int:
    """Insere/actualiza templates no arquivo; devolve quantidade."""
    templates = templates_from_records(load_program_templates_json(path))
    for t in templates:
        archive.upsert_program_template(t)
    return len(templates)
