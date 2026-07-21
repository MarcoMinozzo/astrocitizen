"""Porta de armazenamento de artefatos (FITS, plots, exports)."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class ArtifactStorePort(Protocol):
    """Object storage (SaaS) ou filesystem local (Desktop)."""

    def put(self, local_path: Path, *, key: str) -> str:
        """Persiste ficheiro e devolve URI."""
        ...

    def exists(self, uri: str) -> bool:
        """Indica se o artefato referenciado existe."""
        ...
