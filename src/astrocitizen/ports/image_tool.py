"""Porta para ferramentas externas de imagem (D-011)."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class ImageToolPort(Protocol):
    """Lanca visualizador / processador externo sobre um ficheiro local."""

    def launch(self, path: Path, *, tool_id: str = "default") -> bool:
        """Abre path na ferramenta; True se o processo arrancou."""
        ...
