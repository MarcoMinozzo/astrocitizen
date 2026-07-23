"""Indice de embeddings + rebuild (AC-195)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from astrocitizen.knowledge.embeddings import (
    EmbedderPort,
    default_embedder,
    pack_vector,
)
from astrocitizen.knowledge.scaffold import default_kb_root, load_json
from astrocitizen.shared.timeutil import utc_now_iso


@dataclass
class EmbedIndexReport:
    n_rows: int
    model_id: str
    dim: int
    built_utc: str


def rebuild_embeddings(
    archive: Any,
    *,
    embedder: EmbedderPort | None = None,
    kb_root: Path | None = None,
    update_manifest: bool = True,
) -> EmbedIndexReport:
    """Gera/actualiza vectores para todos os chunks activos."""
    emb = embedder or default_embedder()
    chunks = archive.list_knowledge_chunks()
    n = archive.upsert_knowledge_embeddings(
        [
            {
                "chunk_id": c.id,
                "model_id": emb.model_id,
                "dim": emb.dim,
                "vector": pack_vector(emb.embed(f"{c.title or ''}\n{c.body or ''}")),
            }
            for c in chunks
        ],
        model_id=emb.model_id,
    )
    report = EmbedIndexReport(
        n_rows=n,
        model_id=emb.model_id,
        dim=emb.dim,
        built_utc=utc_now_iso(),
    )
    if update_manifest:
        _update_manifest_embeddings(kb_root or default_kb_root(), report)
    return report


def _utc_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _update_manifest_embeddings(kb_root: Path, report: EmbedIndexReport) -> None:
    path = Path(kb_root) / "manifest.json"
    if not path.is_file():
        return
    manifest = load_json(path)
    index = dict(manifest.get("index") or {})
    if "fts" not in index:
        index["fts"] = None
    index["embeddings"] = {
        "engine": "sqlite-blob",
        "model_id": report.model_id,
        "dim": report.dim,
        "built_utc": report.built_utc,
        "n_rows": report.n_rows,
    }
    manifest["index"] = index
    manifest["phase"] = "KB-4"
    manifest["updated_utc"] = _utc_date()
    path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
