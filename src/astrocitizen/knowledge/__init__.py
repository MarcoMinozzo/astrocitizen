"""E19 knowledge-base package (scaffold KB-0 + schema AC-191)."""

from astrocitizen.knowledge.models import KnowledgeChunk, KnowledgeDocument
from astrocitizen.knowledge.scaffold import default_kb_root, validate_kb_scaffold

__all__ = [
    "KnowledgeChunk",
    "KnowledgeDocument",
    "default_kb_root",
    "validate_kb_scaffold",
]
