"""AC-199: gold questions citation rate eval."""

from __future__ import annotations

import json
from pathlib import Path

from astrocitizen.adapters.sqlite import HybridRetriever, SqliteArchive
from astrocitizen.knowledge.eval_gold import evaluate_gold, load_gold_questions
from astrocitizen.knowledge.models import KnowledgeChunk, KnowledgeDocument


def test_load_gold_set() -> None:
    data = load_gold_questions()
    assert data.get("status") == "active"
    assert float(data.get("citation_rate_target") or 0) >= 0.8
    assert len(data.get("questions") or []) >= 10


def test_evaluate_gold_synthetic(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "g.sqlite3")
    archive.migrate()
    archive.upsert_knowledge_document(
        KnowledgeDocument(
            id="docs-analise-espectral",
            source_id="docs-analise-espectral",
            path="a.md",
            title="A",
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
            body="AC-106 spectrum-report nao substitui fotometria.",
            trust_tier="T3",
            chunk_hash="sha256:1",
            title="AC-106",
            topics=["spectrum"],
        )
    )
    archive.rebuild_knowledge_fts()

    kb = tmp_path / "knowledge-base"
    (kb / "qa").mkdir(parents=True)
    (kb / "qa" / "gold-questions.v0.json").write_text(
        json.dumps(
            {
                "set_id": "mini",
                "citation_rate_target": 0.5,
                "questions": [
                    {
                        "id": "Q1",
                        "question": "AC-106 spectrum-report fotometria",
                        "expected_source_ids": ["docs-analise-espectral"],
                    },
                    {
                        "id": "Q2",
                        "question": "zzz_no_match_token_xyz",
                        "expected_source_ids": ["docs-analise-espectral"],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    report = evaluate_gold(
        HybridRetriever(archive), kb_root=kb, mode="fts", limit=3
    )
    assert report.n_questions == 2
    assert report.n_hits == 1
    assert report.citation_rate == 0.5
    assert report.passed
    archive.close()
