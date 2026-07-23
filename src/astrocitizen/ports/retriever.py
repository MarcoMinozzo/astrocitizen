"""Porta de retrieval da base de conhecimento (E19 / AC-194)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class RetrieveFilters:
    """Filtros opcionais sobre o corpus (PO-*, rede, topic, lang, …)."""

    trust_tier: str | None = None
    source_id: str | None = None
    lang: str | None = None
    po_id: str | None = None
    network: str | None = None
    topic: str | None = None


@dataclass
class Citation:
    """Passagem citavel — sempre com chunk_id / source_id / trust_tier."""

    chunk_id: str
    source_id: str
    trust_tier: str
    title: str | None = None
    snippet: str = ""
    body: str | None = None
    score: float | None = None
    path: str | None = None
    lang: str | None = None
    po_id: str | None = None
    network: str | None = None
    topics: list[str] = field(default_factory=list)
    chunk_hash: str | None = None

    def citation_label(self) -> str:
        return f"{self.chunk_id} ({self.source_id}, {self.trust_tier})"


@runtime_checkable
class RetrieverPort(Protocol):
    """Retrieval lexical/hibrido sem LLM — so passagens + metadados."""

    def search(
        self,
        query: str,
        *,
        limit: int = 10,
        filters: RetrieveFilters | None = None,
    ) -> list[Citation]:
        """Devolve passagens ordenadas por relevancia (score menor = melhor em FTS bm25)."""
        ...

    def get_chunk(self, chunk_id: str) -> Citation | None:
        """Obtem um chunk completo por id (citacao + body)."""
        ...

    def list_sources(
        self,
        *,
        trust_tier: str | None = None,
    ) -> list[dict[str, Any]]:
        """Lista fontes/documentos ingeridos (id, title, trust_tier, …)."""
        ...
