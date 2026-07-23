"""E19 knowledge-base package (scaffold + schema + ingest)."""

from astrocitizen.knowledge.ingest import IngestReport, ingest_sources
from astrocitizen.knowledge.models import KnowledgeChunk, KnowledgeDocument
from astrocitizen.knowledge.scaffold import default_kb_root, validate_kb_scaffold

__all__ = [
    "IngestReport",
    "KnowledgeChunk",
    "KnowledgeDocument",
    "default_kb_root",
    "ingest_sources",
    "validate_kb_scaffold",
]
