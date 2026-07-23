"""Modelos E19: documentos e chunks da base de conhecimento (AC-191)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class KnowledgeDocument:
    """Fonte / documento do corpus KB (chave = source_id)."""

    id: str
    source_id: str
    path: str
    title: str
    trust_tier: str
    license_id: str | None = None
    lang: str | None = None
    topics: list[str] = field(default_factory=list)
    networks: list[str] = field(default_factory=list)
    content_hash: str | None = None
    corpus_version: str | None = None
    status: str = "planned"
    created_at: str = ""
    updated_at: str = ""
    version: int = 1


@dataclass
class KnowledgeChunk:
    """Chunk citavel (chunk_id + source_id + trust_tier + hash)."""

    id: str
    document_id: str
    source_id: str
    body: str
    trust_tier: str
    chunk_hash: str
    path: str | None = None
    title: str | None = None
    lang: str | None = None
    topics: list[str] = field(default_factory=list)
    po_id: str | None = None
    network: str | None = None
    pipeline_stage: str | None = None
    token_estimate: int | None = None
    corpus_version: str | None = None
    sort_order: int = 0
    created_at: str = ""
    updated_at: str = ""
    version: int = 1
