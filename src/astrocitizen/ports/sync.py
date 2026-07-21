"""Portas de sincronizacao e exportacao a redes."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class SyncPort(Protocol):
    """Cliente ou servidor de sync Desktop <-> SaaS."""

    def pull_changes(self, *, cursor: str | None) -> dict[str, Any]:
        """Obtem alteracoes desde o cursor."""
        ...

    def push_batch(self, operations: list[dict[str, Any]]) -> dict[str, Any]:
        """Envia lote de operacoes (idempotente)."""
        ...


@runtime_checkable
class NetworkExportPort(Protocol):
    """Exportacao para redes cidadas (AAVSO, MPC, ...)."""

    def validate(self, *, network: str, payload: dict[str, Any]) -> bool:
        """Valida payload contra atlas / produto minimo."""
        ...
