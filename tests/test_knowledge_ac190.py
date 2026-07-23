"""AC-190: knowledge-base KB-0 scaffold."""

from __future__ import annotations

from astrocitizen.knowledge import default_kb_root, validate_kb_scaffold


def test_kb_scaffold_valid() -> None:
    root = default_kb_root()
    assert root.is_dir()
    errors = validate_kb_scaffold(root)
    assert errors == [], errors


def test_catalog_has_t3_sources() -> None:
    import json

    catalog = json.loads((default_kb_root() / "catalog.json").read_text(encoding="utf-8"))
    tiers = {s["trust_tier"] for s in catalog["sources"]}
    assert "T3" in tiers
