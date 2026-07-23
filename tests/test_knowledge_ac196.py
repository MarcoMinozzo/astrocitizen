"""AC-196: Ajuda grounded so com citacoes."""

from __future__ import annotations

from pathlib import Path

from astrocitizen.adapters.sqlite import HybridRetriever, SqliteArchive
from astrocitizen.knowledge.assistant import answer_help
from astrocitizen.knowledge.models import KnowledgeChunk, KnowledgeDocument


def _seed(archive: SqliteArchive) -> None:
    archive.upsert_knowledge_document(
        KnowledgeDocument(
            id="docs-analise-espectral",
            source_id="docs-analise-espectral",
            path="docs/A.md",
            title="Analise",
            trust_tier="T3",
            lang="pt",
            topics=["spectrum"],
            status="ingested",
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
            chunk_hash="sha256:1",
            title="AC-106",
            lang="pt",
            topics=["spectrum"],
        )
    )
    archive.rebuild_knowledge_fts()


def test_answer_help_grounded_with_citations(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "a.sqlite3")
    archive.migrate()
    _seed(archive)
    ans = answer_help(
        HybridRetriever(archive),
        "AC-106 substitui fotometria?",
        mode="fts",
        limit=3,
    )
    assert ans.grounded
    assert ans.citations
    assert ans.citations[0].chunk_id
    assert ans.citations[0].source_id
    assert ans.citations[0].trust_tier
    text = ans.format_text()
    assert "Citacoes:" in text
    assert "docs-analise-espectral" in text
    archive.close()


def test_answer_help_refuses_without_hits(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "b.sqlite3")
    archive.migrate()
    _seed(archive)
    ans = answer_help(
        HybridRetriever(archive),
        "xyzzy_nonexistent_token_qqq",
        mode="fts",
        limit=3,
    )
    assert not ans.grounded
    assert ans.refusal_reason == "no_hits"
    assert not ans.citations
    archive.close()


def test_answer_help_empty_question(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "c.sqlite3")
    archive.migrate()
    ans = answer_help(HybridRetriever(archive), "  ")
    assert not ans.grounded
    assert ans.refusal_reason == "empty_question"
    archive.close()
