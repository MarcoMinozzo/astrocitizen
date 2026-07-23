"""E19 knowledge-base package (scaffold + ingest + FTS + embeddings)."""

from astrocitizen.knowledge.embed_index import EmbedIndexReport, rebuild_embeddings
from astrocitizen.knowledge.embeddings import HashingNgramEmbedder, default_embedder
from astrocitizen.knowledge.ingest import IngestReport, ingest_sources
from astrocitizen.knowledge.models import KnowledgeChunk, KnowledgeDocument
from astrocitizen.knowledge.scaffold import default_kb_root, validate_kb_scaffold
from astrocitizen.knowledge.search import (
    FtsIndexReport,
    SearchHit,
    rebuild_fts_index,
    search_knowledge,
)

__all__ = [
    "EmbedIndexReport",
    "FtsIndexReport",
    "HashingNgramEmbedder",
    "IngestReport",
    "KnowledgeChunk",
    "KnowledgeDocument",
    "SearchHit",
    "default_embedder",
    "default_kb_root",
    "ingest_sources",
    "rebuild_embeddings",
    "rebuild_fts_index",
    "search_knowledge",
    "validate_kb_scaffold",
]
