"""AC-200: spectrum_report + RAG explain."""

from __future__ import annotations

from pathlib import Path

from astrocitizen.adapters.sqlite import HybridRetriever, SqliteArchive
from astrocitizen.knowledge.models import KnowledgeChunk, KnowledgeDocument
from astrocitizen.knowledge.spectrum_explain import (
    build_spectrum_query,
    explain_spectrum_report,
    extract_report_cues,
)


SAMPLE_REPORT = """
#TYPE=ASTROCITIZEN_SPECTRUM_REPORT
class_hint: Be / emission
top_line: H-alpha
FEATURES:
- H-alpha emission SNR=12.1
- H-beta emission SNR=5.2
- O2 A (telluric) absorption
- He I 5876 weak
BeSS / ARAS style citizen interpretation.
"""


def test_extract_cues_and_query() -> None:
    cues = extract_report_cues(SAMPLE_REPORT)
    assert "H-alpha" in cues["features"]
    assert cues["class_hint"]
    q = build_spectrum_query(cues)
    assert "BeSS" in q
    assert "H-alpha" in q


def test_explain_spectrum_grounded(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "s.sqlite3")
    archive.migrate()
    archive.upsert_knowledge_document(
        KnowledgeDocument(
            id="docs-analise-espectral",
            source_id="docs-analise-espectral",
            path="a.md",
            title="Analise",
            trust_tier="T3",
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
                "AC-106 spectrum_report BeSS ARAS. H-alpha emission em Be stars. "
                "Nao inventar linhas fora do relatorio."
            ),
            trust_tier="T3",
            chunk_hash="sha256:1",
            title="BeSS",
            topics=["spectrum"],
            network="bess",
        )
    )
    archive.rebuild_knowledge_fts()
    result = explain_spectrum_report(
        HybridRetriever(archive), SAMPLE_REPORT, mode="fts", limit=3
    )
    assert result.grounded
    assert result.features_used
    assert result.citations
    assert "AC-106" in result.format_text() or "FEATURES" in result.format_text()
    assert "Citacoes KB" in result.format_text()
    archive.close()


def test_explain_empty_report(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "e.sqlite3")
    archive.migrate()
    result = explain_spectrum_report(HybridRetriever(archive), "  ")
    assert not result.grounded
    archive.close()
