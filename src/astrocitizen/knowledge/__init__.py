"""E19 knowledge-base package (scaffold + schema + ingest + FTS)."""

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
    "FtsIndexReport",
    "IngestReport",
    "KnowledgeChunk",
    "KnowledgeDocument",
    "SearchHit",
    "default_kb_root",
    "ingest_sources",
    "rebuild_fts_index",
    "search_knowledge",
    "validate_kb_scaffold",
]
