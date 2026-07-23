"""AC-195: embeddings locais + RRF hibrido."""

from __future__ import annotations

import json
from pathlib import Path

from astrocitizen.adapters.sqlite import HybridRetriever, SqliteArchive
from astrocitizen.adapters.sqlite.schema import SCHEMA_VERSION
from astrocitizen.knowledge.embed_index import rebuild_embeddings
from astrocitizen.knowledge.embeddings import (
    HashingNgramEmbedder,
    cosine_similarity,
    rrf_fuse,
)
from astrocitizen.knowledge.models import KnowledgeChunk, KnowledgeDocument
from astrocitizen.ports.retriever import RetrieveFilters


def _seed(archive: SqliteArchive) -> None:
    archive.upsert_knowledge_document(
        KnowledgeDocument(
            id="docs-a",
            source_id="docs-a",
            path="docs/a.md",
            title="A",
            trust_tier="T3",
            lang="pt",
            topics=["spectrum"],
            status="ingested",
        )
    )
    archive.upsert_knowledge_document(
        KnowledgeDocument(
            id="docs-b",
            source_id="docs-b",
            path="docs/b.md",
            title="B",
            trust_tier="T3",
            lang="pt",
            topics=["workflows"],
            status="ingested",
        )
    )
    archive.upsert_knowledge_chunk(
        KnowledgeChunk(
            id="docs-a-001",
            document_id="docs-a",
            source_id="docs-a",
            body="AC-106 interpretacao espectral deterministica spectrum-report linhas.",
            trust_tier="T3",
            chunk_hash="sha256:a",
            title="Spectrum",
            lang="pt",
            topics=["spectrum"],
        )
    )
    archive.upsert_knowledge_chunk(
        KnowledgeChunk(
            id="docs-b-001",
            document_id="docs-b",
            source_id="docs-b",
            body="Workflows de navegacao desktop e programas observacionais.",
            trust_tier="T3",
            chunk_hash="sha256:b",
            title="UX",
            lang="pt",
            topics=["workflows"],
        )
    )
    archive.rebuild_knowledge_fts()


def test_schema_v8_embeddings_table(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "e.sqlite3")
    assert archive.migrate() == SCHEMA_VERSION
    assert SCHEMA_VERSION >= 8
    names = {
        r[0]
        for r in archive._conn.execute(
            "SELECT name FROM sqlite_master WHERE name LIKE 'knowledge%'"
        ).fetchall()
    }
    assert "knowledge_chunk_embeddings" in names
    archive.close()


def test_hashing_embedder_cosine() -> None:
    emb = HashingNgramEmbedder(dim=128)
    a = emb.embed("spectrum report linhas espectrais AC-106")
    b = emb.embed("spectrum report linhas espectrais AC-106")
    c = emb.embed("navegacao desktop workflows programas")
    assert cosine_similarity(a, b) > 0.99
    assert cosine_similarity(a, c) < cosine_similarity(a, b)


def test_rrf_fuse_order() -> None:
    fused = rrf_fuse([["a", "b", "c"], ["b", "a", "d"]], k=60, limit=3)
    ids = [x[0] for x in fused]
    assert ids[0] in {"a", "b"}
    assert "c" in ids or "d" in ids


def test_hybrid_retriever(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "h.sqlite3")
    archive.migrate()
    _seed(archive)
    kb = tmp_path / "knowledge-base"
    kb.mkdir()
    (kb / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "corpus_version": "0.1.0-kb1",
                "phase": "KB-2",
                "index": {"fts": {"n_rows": 2}, "embeddings": None},
            }
        ),
        encoding="utf-8",
    )
    report = rebuild_embeddings(archive, kb_root=kb, update_manifest=True)
    assert report.n_rows == 2
    manifest = json.loads((kb / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["phase"] == "KB-4"
    assert manifest["index"]["embeddings"]["n_rows"] == 2

    r = HybridRetriever(archive)
    fts = r.search("spectrum AC-106", mode="fts", limit=5)
    assert fts and fts[0].source_id == "docs-a"
    vec = r.search("spectrum AC-106", mode="vector", limit=5)
    assert vec and vec[0].chunk_id == "docs-a-001"
    hyb = r.search(
        "spectrum AC-106",
        mode="hybrid",
        limit=5,
        filters=RetrieveFilters(trust_tier="T3"),
    )
    assert hyb and any(h.chunk_id == "docs-a-001" for h in hyb)
    archive.close()
