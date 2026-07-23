"""Retriever hibrido FTS + embeddings com RRF (AC-195)."""

from __future__ import annotations

from typing import Any, Literal

from astrocitizen.adapters.sqlite.fts_retriever import SqliteFtsRetriever
from astrocitizen.knowledge.embeddings import (
    EmbedderPort,
    cosine_similarity,
    default_embedder,
    rrf_fuse,
    unpack_vector,
)
from astrocitizen.ports.retriever import Citation, RetrieveFilters

SearchMode = Literal["fts", "vector", "hybrid"]


class HybridRetriever:
    """FTS5 + cosine local + RRF. Fallback automatico para FTS se sem embeddings."""

    def __init__(
        self,
        archive: Any,
        *,
        embedder: EmbedderPort | None = None,
        rrf_k: int = 60,
        candidate_pool: int = 40,
    ) -> None:
        self._archive = archive
        self._fts = SqliteFtsRetriever(archive)
        self._embedder = embedder or default_embedder()
        self._rrf_k = int(rrf_k)
        self._pool = max(5, int(candidate_pool))

    def search(
        self,
        query: str,
        *,
        limit: int = 10,
        filters: RetrieveFilters | None = None,
        mode: SearchMode = "hybrid",
    ) -> list[Citation]:
        lim = max(1, min(int(limit or 10), 100))
        mode_n = (mode or "hybrid").lower()
        if mode_n == "fts":
            return self._fts.search(query, limit=lim, filters=filters)
        if mode_n == "vector":
            return self._vector_search(query, limit=lim, filters=filters)
        # hybrid
        fts_hits = self._fts.search(query, limit=self._pool, filters=filters)
        vec_hits = self._vector_search(query, limit=self._pool, filters=filters)
        if not vec_hits:
            return fts_hits[:lim]
        if not fts_hits:
            return vec_hits[:lim]
        fused = rrf_fuse(
            [
                [h.chunk_id for h in fts_hits],
                [h.chunk_id for h in vec_hits],
            ],
            k=self._rrf_k,
            limit=lim,
        )
        by_id: dict[str, Citation] = {h.chunk_id: h for h in fts_hits}
        for h in vec_hits:
            by_id.setdefault(h.chunk_id, h)
        out: list[Citation] = []
        for chunk_id, score in fused:
            base = by_id.get(chunk_id)
            if base is None:
                loaded = self.get_chunk(chunk_id)
                if loaded is None:
                    continue
                base = loaded
            out.append(
                Citation(
                    chunk_id=base.chunk_id,
                    source_id=base.source_id,
                    trust_tier=base.trust_tier,
                    title=base.title,
                    snippet=base.snippet,
                    body=None,
                    score=score,
                    path=base.path,
                    lang=base.lang,
                    po_id=base.po_id,
                    network=base.network,
                    topics=list(base.topics or []),
                    chunk_hash=base.chunk_hash,
                )
            )
        return out

    def get_chunk(self, chunk_id: str) -> Citation | None:
        return self._fts.get_chunk(chunk_id)

    def list_sources(
        self,
        *,
        trust_tier: str | None = None,
    ) -> list[dict[str, Any]]:
        return self._fts.list_sources(trust_tier=trust_tier)

    def _vector_search(
        self,
        query: str,
        *,
        limit: int,
        filters: RetrieveFilters | None,
    ) -> list[Citation]:
        rows = self._archive.list_knowledge_embeddings(model_id=self._embedder.model_id)
        if not rows:
            return []
        q = self._embedder.embed(query)
        f = filters or RetrieveFilters()
        scored: list[tuple[float, dict[str, Any]]] = []
        for row in rows:
            try:
                vec = unpack_vector(row["vector"], int(row["dim"]))
            except ValueError:
                continue
            sim = cosine_similarity(q, vec)
            scored.append((sim, row))
        scored.sort(key=lambda t: (-t[0], t[1]["chunk_id"]))
        out: list[Citation] = []
        for sim, row in scored:
            if len(out) >= limit:
                break
            cite = self.get_chunk(row["chunk_id"])
            if cite is None:
                continue
            if f.trust_tier and cite.trust_tier != f.trust_tier:
                continue
            if f.source_id and cite.source_id != f.source_id:
                continue
            if f.lang and cite.lang != f.lang:
                continue
            if f.po_id and cite.po_id != f.po_id:
                continue
            if f.network and cite.network != f.network:
                continue
            if f.topic and f.topic not in (cite.topics or []):
                continue
            cite.score = sim
            cite.snippet = (cite.body or "")[:160].replace("\n", " ")
            cite.body = None
            out.append(cite)
        return out
