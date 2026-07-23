"""AC-193: FTS5 + knowledge search."""

from __future__ import annotations

import json
from pathlib import Path

from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.adapters.sqlite.schema import SCHEMA_VERSION
from astrocitizen.knowledge.models import KnowledgeChunk, KnowledgeDocument
from astrocitizen.knowledge.search import (
    build_fts_query,
    rebuild_fts_index,
    search_knowledge,
)


def test_schema_v7_fts_table(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "fts.sqlite3")
    assert archive.migrate() == SCHEMA_VERSION
    assert SCHEMA_VERSION >= 7
    names = {
        r[0]
        for r in archive._conn.execute(
            "SELECT name FROM sqlite_master WHERE name LIKE 'knowledge%'"
        ).fetchall()
    }
    assert "knowledge_chunks_fts" in names
    archive.close()


def test_build_fts_query_tokens() -> None:
    q = build_fts_query("Quais sao as areas da navegacao desktop?")
    assert "areas" in q.lower() or "navegacao" in q.lower() or "desktop" in q.lower()
    assert "OR" in q
    assert build_fts_query("  ") == ""


def test_fold_corrupt_accents() -> None:
    from astrocitizen.knowledge.search import fold_corrupt_accents

    # U+00FF (ÿ) como em WORKFLOWS.md corrompido
    assert "navegacao" not in fold_corrupt_accents("navega\u00ff\u00ffo")  # perde ç
    assert "navegao" in fold_corrupt_accents("navega\u00ff\u00ffo")
    assert "reducao" in fold_corrupt_accents("redução").lower()
    assert fold_corrupt_accents("Café") == "Cafe"


def test_fts_rebuild_and_search(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "kb.sqlite3")
    archive.migrate()
    archive.upsert_knowledge_document(
        KnowledgeDocument(
            id="docs-workflows",
            source_id="docs-workflows",
            path="docs/WORKFLOWS.md",
            title="Workflows",
            trust_tier="T3",
            lang="pt",
            topics=["ux", "workflows"],
            status="ingested",
        )
    )
    archive.upsert_knowledge_document(
        KnowledgeDocument(
            id="docs-analise-espectral",
            source_id="docs-analise-espectral",
            path="docs/ANALISE_ESPECTRAL_ASSISTIDA.md",
            title="Analise espectral",
            trust_tier="T3",
            lang="pt",
            topics=["spectrum"],
            status="ingested",
        )
    )
    archive.upsert_knowledge_chunk(
        KnowledgeChunk(
            id="docs-workflows-001",
            document_id="docs-workflows",
            source_id="docs-workflows",
            body=(
                "## Mapa de navegacao\n\n"
                "As seis areas da navegacao desktop: Inicio, Inventario, "
                "Programa, Observatorio, Analise, Contribuicao."
            ),
            trust_tier="T3",
            chunk_hash="sha256:wf1",
            title="Mapa de navegacao",
            lang="pt",
            topics=["ux", "workflows"],
        )
    )
    archive.upsert_knowledge_chunk(
        KnowledgeChunk(
            id="docs-analise-espectral-001",
            document_id="docs-analise-espectral",
            source_id="docs-analise-espectral",
            body=(
                "AC-106 e interpretacao assistida deterministica. "
                "Nao substitui fotometria nem spectrum-report."
            ),
            trust_tier="T3",
            chunk_hash="sha256:ae1",
            title="AC-106",
            lang="pt",
            topics=["spectrum"],
        )
    )

    kb = tmp_path / "knowledge-base"
    kb.mkdir()
    (kb / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "corpus_version": "0.1.0-kb1",
                "phase": "KB-1",
                "n_sources": 2,
                "n_chunks": 2,
                "ingest": {"status": "completed"},
                "index": {"fts": None, "embeddings": None},
            }
        ),
        encoding="utf-8",
    )

    report = rebuild_fts_index(archive, kb_root=kb, update_manifest=True)
    assert report.n_rows == 2
    manifest = json.loads((kb / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["phase"] == "KB-2"
    assert manifest["index"]["fts"]["n_rows"] == 2
    assert manifest["index"]["fts"]["engine"] == "sqlite-fts5"

    hits = search_knowledge(archive, "navegacao desktop areas", limit=5)
    assert hits
    assert hits[0].chunk_id == "docs-workflows-001"
    assert hits[0].source_id == "docs-workflows"
    assert hits[0].trust_tier == "T3"
    assert hits[0].snippet

    hits2 = search_knowledge(
        archive, "AC-106 fotometria spectrum-report", limit=5, trust_tier="T3"
    )
    assert any(h.source_id == "docs-analise-espectral" for h in hits2)

    filtered = search_knowledge(
        archive, "navegacao", source_id="docs-analise-espectral", limit=5
    )
    assert filtered == []

    archive.close()
