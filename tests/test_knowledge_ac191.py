"""AC-191: schema knowledge_documents / knowledge_chunks."""

from __future__ import annotations

from pathlib import Path

import pytest

from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.adapters.sqlite.schema import SCHEMA_VERSION
from astrocitizen.knowledge.models import KnowledgeChunk, KnowledgeDocument
from astrocitizen.shared.errors import NotFoundError


def test_schema_v6_knowledge_tables(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "kb.sqlite3")
    assert archive.migrate() == SCHEMA_VERSION
    assert SCHEMA_VERSION >= 6
    tables = {
        r[0]
        for r in archive._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    assert "knowledge_documents" in tables
    assert "knowledge_chunks" in tables
    # idempotent
    assert archive.migrate() == SCHEMA_VERSION
    archive.close()


def test_knowledge_document_and_chunk_crud(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "kb2.sqlite3")
    archive.migrate()
    doc = archive.upsert_knowledge_document(
        KnowledgeDocument(
            id="docs-workflows",
            source_id="docs-workflows",
            path="docs/WORKFLOWS.md",
            title="Workflows",
            trust_tier="T3",
            lang="pt",
            topics=["workflows"],
            content_hash="sha256:doc1",
            corpus_version="0.0.1",
            status="ingested",
        )
    )
    assert doc.source_id == "docs-workflows"
    got = archive.get_knowledge_document("docs-workflows")
    assert got is not None
    assert got.trust_tier == "T3"
    assert got.topics == ["workflows"]
    assert archive.list_knowledge_documents(trust_tier="T3")

    chunk = archive.upsert_knowledge_chunk(
        KnowledgeChunk(
            id="SRC-0001",
            document_id="docs-workflows",
            source_id="docs-workflows",
            body="Modo Contribuir: Revisar campos.",
            trust_tier="T3",
            chunk_hash="sha256:chunk1",
            path="docs/WORKFLOWS.md",
            title="Contribuir",
            lang="pt",
            topics=["workflows"],
            pipeline_stage="help",
            token_estimate=40,
            corpus_version="0.0.1",
            sort_order=1,
        )
    )
    assert chunk.id == "SRC-0001"
    loaded = archive.get_knowledge_chunk("SRC-0001")
    assert loaded is not None
    assert loaded.chunk_hash == "sha256:chunk1"
    assert loaded.source_id == "docs-workflows"
    assert loaded.body.startswith("Modo Contribuir")
    listed = archive.list_knowledge_chunks(source_id="docs-workflows")
    assert len(listed) == 1

    archive.soft_delete_knowledge_chunk("SRC-0001")
    assert archive.get_knowledge_chunk("SRC-0001") is None

    archive.upsert_knowledge_chunk(
        KnowledgeChunk(
            id="SRC-0002",
            document_id="docs-workflows",
            source_id="docs-workflows",
            body="segundo",
            trust_tier="T3",
            chunk_hash="sha256:chunk2",
        )
    )
    archive.soft_delete_knowledge_document("docs-workflows")
    assert archive.get_knowledge_document("docs-workflows") is None
    assert archive.list_knowledge_chunks(source_id="docs-workflows") == []
    archive.close()


def test_chunk_requires_document(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "kb3.sqlite3")
    archive.migrate()
    with pytest.raises(NotFoundError):
        archive.upsert_knowledge_chunk(
            KnowledgeChunk(
                id="orphan",
                document_id="missing",
                source_id="missing",
                body="x",
                trust_tier="T3",
                chunk_hash="sha256:x",
            )
        )
    archive.close()
