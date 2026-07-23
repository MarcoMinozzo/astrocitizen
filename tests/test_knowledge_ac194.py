"""AC-194: RetrieverPort + filtros."""

from __future__ import annotations

from pathlib import Path

from astrocitizen.adapters.sqlite import SqliteArchive, SqliteFtsRetriever
from astrocitizen.knowledge.models import KnowledgeChunk, KnowledgeDocument
from astrocitizen.ports.retriever import Citation, RetrieveFilters, RetrieverPort


def _seed(archive: SqliteArchive) -> None:
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
            id="docs-entrada",
            source_id="docs-entrada",
            path="docs/ENTRADA.md",
            title="Entrada",
            trust_tier="T3",
            lang="pt",
            topics=["entrada", "programs"],
            status="ingested",
        )
    )
    archive.upsert_knowledge_chunk(
        KnowledgeChunk(
            id="docs-workflows-001",
            document_id="docs-workflows",
            source_id="docs-workflows",
            body="Mapa de navegacao desktop com seis areas e UX.",
            trust_tier="T3",
            chunk_hash="sha256:a",
            title="Navegacao",
            lang="pt",
            topics=["ux", "workflows"],
            po_id=None,
            network=None,
        )
    )
    archive.upsert_knowledge_chunk(
        KnowledgeChunk(
            id="docs-entrada-001",
            document_id="docs-entrada",
            source_id="docs-entrada",
            body="Produto double_measure PO-G01 para medidas de duplas WDS.",
            trust_tier="T3",
            chunk_hash="sha256:b",
            title="Duplas",
            lang="pt",
            topics=["entrada", "programs"],
            po_id="PO-G01",
            network="wds",
        )
    )
    archive.rebuild_knowledge_fts()


def test_retriever_port_protocol(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "r.sqlite3")
    archive.migrate()
    _seed(archive)
    retriever: RetrieverPort = SqliteFtsRetriever(archive)
    hits = retriever.search("navegacao desktop", limit=5)
    assert hits
    assert isinstance(hits[0], Citation)
    assert hits[0].chunk_id
    assert hits[0].source_id
    assert hits[0].trust_tier
    assert "docs-workflows" in hits[0].citation_label()

    cite = retriever.get_chunk("docs-entrada-001")
    assert cite is not None
    assert cite.body and "double_measure" in cite.body
    assert cite.po_id == "PO-G01"

    sources = retriever.list_sources(trust_tier="T3")
    assert {s["source_id"] for s in sources} >= {"docs-workflows", "docs-entrada"}
    archive.close()


def test_retriever_filters_topic_po_network(tmp_path: Path) -> None:
    archive = SqliteArchive(tmp_path / "f.sqlite3")
    archive.migrate()
    _seed(archive)
    r = SqliteFtsRetriever(archive)

    by_topic = r.search(
        "duplas measure",
        filters=RetrieveFilters(topic="entrada"),
        limit=5,
    )
    assert by_topic
    assert all("entrada" in h.topics for h in by_topic)

    by_po = r.search(
        "double_measure",
        filters=RetrieveFilters(po_id="PO-G01"),
        limit=5,
    )
    assert by_po and by_po[0].chunk_id == "docs-entrada-001"

    by_net = r.search(
        "WDS duplas",
        filters=RetrieveFilters(network="wds", lang="pt"),
        limit=5,
    )
    assert by_net and by_net[0].network == "wds"

    miss = r.search(
        "navegacao",
        filters=RetrieveFilters(topic="spectrum"),
        limit=5,
    )
    assert miss == []
    archive.close()
