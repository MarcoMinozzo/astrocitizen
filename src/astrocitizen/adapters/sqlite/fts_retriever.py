"""Adapter RetrieverPort sobre SQLite FTS5 (AC-194)."""

from __future__ import annotations

from typing import Any

from astrocitizen.ports.retriever import Citation, RetrieveFilters


class SqliteFtsRetriever:
    """Implementacao Desktop-first: FTS5 via SqliteArchive."""

    def __init__(self, archive: Any) -> None:
        self._archive = archive

    def search(
        self,
        query: str,
        *,
        limit: int = 10,
        filters: RetrieveFilters | None = None,
    ) -> list[Citation]:
        f = filters or RetrieveFilters()
        rows = self._archive.search_knowledge_chunks(
            query,
            limit=limit,
            trust_tier=f.trust_tier,
            source_id=f.source_id,
            lang=f.lang,
            po_id=f.po_id,
            network=f.network,
            topic=f.topic,
        )
        return [_row_to_citation(r, include_body=False) for r in rows]

    def get_chunk(self, chunk_id: str) -> Citation | None:
        chunk = self._archive.get_knowledge_chunk(chunk_id)
        if chunk is None:
            return None
        return Citation(
            chunk_id=chunk.id,
            source_id=chunk.source_id,
            trust_tier=chunk.trust_tier,
            title=chunk.title,
            snippet="",
            body=chunk.body,
            score=None,
            path=chunk.path,
            lang=chunk.lang,
            po_id=chunk.po_id,
            network=chunk.network,
            topics=list(chunk.topics or []),
            chunk_hash=chunk.chunk_hash,
        )

    def list_sources(
        self,
        *,
        trust_tier: str | None = None,
    ) -> list[dict[str, Any]]:
        docs = self._archive.list_knowledge_documents(
            trust_tier=trust_tier, status="ingested"
        )
        out: list[dict[str, Any]] = []
        for d in docs:
            out.append(
                {
                    "source_id": d.source_id,
                    "title": d.title,
                    "trust_tier": d.trust_tier,
                    "path": d.path,
                    "lang": d.lang,
                    "topics": list(d.topics or []),
                    "status": d.status,
                }
            )
        return out


def _row_to_citation(row: dict[str, Any], *, include_body: bool) -> Citation:
    return Citation(
        chunk_id=str(row["chunk_id"]),
        source_id=str(row["source_id"]),
        trust_tier=str(row["trust_tier"]),
        title=row.get("title"),
        snippet=str(row.get("snippet") or ""),
        body=str(row["body"]) if include_body and row.get("body") is not None else None,
        score=float(row["score"]) if row.get("score") is not None else None,
        path=row.get("path"),
        lang=row.get("lang"),
        po_id=row.get("po_id"),
        network=row.get("network"),
        topics=list(row.get("topics") or []),
        chunk_hash=row.get("chunk_hash"),
    )
