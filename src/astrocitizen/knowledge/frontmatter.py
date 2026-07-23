"""Frontmatter YAML simples para chunks KB (AC-192)."""

from __future__ import annotations

import json
from typing import Any


def _yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=False)
    text = str(value)
    if any(c in text for c in (":", "#", "{", "}", "[", "]", ",", "\n")) or text == "":
        escaped = text.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return text


def render_chunk_markdown(meta: dict[str, Any], body: str) -> str:
    """Gera ficheiro no formato templates/chunk.md."""
    order = (
        "chunk_id",
        "source_id",
        "path",
        "title",
        "trust_tier",
        "lang",
        "topics",
        "po_id",
        "network",
        "pipeline_stage",
        "token_estimate",
        "chunk_hash",
        "corpus_version",
    )
    lines = ["---"]
    for key in order:
        if key in meta:
            lines.append(f"{key}: {_yaml_scalar(meta[key])}")
    for key, val in meta.items():
        if key not in order:
            lines.append(f"{key}: {_yaml_scalar(val)}")
    lines.append("---")
    lines.append("")
    lines.append((body or "").rstrip())
    lines.append("")
    return "\n".join(lines)
