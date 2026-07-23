"""Knowledge-base scaffold helpers (E19 / AC-190 KB-0)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REQUIRED_FILES: tuple[str, ...] = (
    "README.md",
    "catalog.json",
    "taxonomy.json",
    "manifest.json",
    "conflict-policy.md",
    "licenses/licenses.json",
    "templates/chunk.md",
    "qa/gold-questions.v0.json",
)

REQUIRED_DIRS: tuple[str, ...] = (
    "licenses",
    "templates",
    "qa",
    "processed",
    "chunks",
    "chunks/v1",
)


def default_kb_root() -> Path:
    """Raiz knowledge-base/ relativa ao repo (pai de src/)."""
    # src/astrocitizen/knowledge/scaffold.py -> parents[3] = repo root
    return Path(__file__).resolve().parents[3] / "knowledge-base"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_kb_scaffold(root: Path | None = None) -> list[str]:
    """Valida layout KB-0; devolve lista de erros (vazia = OK)."""
    kb = Path(root) if root is not None else default_kb_root()
    errors: list[str] = []
    if not kb.is_dir():
        return [f"missing knowledge-base root: {kb}"]
    for d in REQUIRED_DIRS:
        if not (kb / d).is_dir():
            errors.append(f"missing dir: {d}")
    for rel in REQUIRED_FILES:
        if not (kb / rel).is_file():
            errors.append(f"missing file: {rel}")
    if errors:
        return errors

    catalog = load_json(kb / "catalog.json")
    taxonomy = load_json(kb / "taxonomy.json")
    manifest = load_json(kb / "manifest.json")
    licenses = load_json(kb / "licenses" / "licenses.json")
    gold = load_json(kb / "qa" / "gold-questions.v0.json")

    if catalog.get("schema_version") != 1:
        errors.append("catalog.schema_version must be 1")
    sources = catalog.get("sources")
    if not isinstance(sources, list) or len(sources) < 1:
        errors.append("catalog.sources must be a non-empty list")
    else:
        ids = [s.get("source_id") for s in sources if isinstance(s, dict)]
        if len(ids) != len(set(ids)):
            errors.append("catalog.source_id duplicates")
        license_ids = {
            lic.get("license_id")
            for lic in (licenses.get("licenses") or [])
            if isinstance(lic, dict)
        }
        tiers = set((taxonomy.get("trust_tiers") or {}).keys())
        for src in sources:
            if not isinstance(src, dict):
                continue
            sid = src.get("source_id")
            if src.get("license_id") not in license_ids:
                errors.append(f"source {sid}: unknown license_id")
            if src.get("trust_tier") not in tiers:
                errors.append(f"source {sid}: unknown trust_tier")
            path = src.get("path")
            if path and not (kb.parent / str(path)).is_file():
                errors.append(f"source {sid}: path not found: {path}")

    if taxonomy.get("schema_version") != 1:
        errors.append("taxonomy.schema_version must be 1")
    for key in ("trust_tiers", "topics", "networks", "pipeline_stages"):
        if key not in taxonomy:
            errors.append(f"taxonomy missing {key}")

    if manifest.get("phase") != "KB-0" and manifest.get("n_chunks", 0) == 0:
        # allow future phases; KB-0 expects phase marker or zero chunks
        pass
    if "corpus_version" not in manifest:
        errors.append("manifest.corpus_version missing")

    if not isinstance(gold.get("questions"), list):
        errors.append("gold-questions.questions must be a list")

    chunk_tpl = (kb / "templates" / "chunk.md").read_text(encoding="utf-8")
    for needle in ("chunk_id:", "source_id:", "trust_tier:", "chunk_hash:"):
        if needle not in chunk_tpl:
            errors.append(f"chunk template missing {needle}")

    return errors
