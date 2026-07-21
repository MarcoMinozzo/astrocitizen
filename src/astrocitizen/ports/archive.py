"""Porta de arquivo / persistencia de dominio (BD mestre ou espelho)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ArchivePort(Protocol):
    """Persistencia de entidades de dominio (RN-110...116).

    Implementacoes: SQLite (Desktop), PostgreSQL (SaaS). Detalhe: MODELO_DADOS_V1.
    """

    def healthcheck(self) -> bool:
        """Retorna True se a ligacao ao arquivo estiver operacional."""
        ...
