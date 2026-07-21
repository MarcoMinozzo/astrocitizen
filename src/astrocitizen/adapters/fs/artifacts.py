"""ArtifactStore local em filesystem (Desktop)."""

from __future__ import annotations

import shutil
from pathlib import Path
from urllib.parse import unquote, urlparse

from astrocitizen.shared.errors import DomainError, NotFoundError


class LocalArtifactStore:
    """Armazena artefactos sob um directorio raiz; URI = file://..."""

    def __init__(self, root: Path) -> None:
        self.root = root.expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, local_path: Path, *, key: str) -> str:
        src = local_path.expanduser().resolve()
        if not src.is_file():
            raise NotFoundError(f"ficheiro nao encontrado: {src}")
        # Normaliza key (sem leading /)
        safe_key = key.lstrip("/").replace("\\", "/")
        if ".." in Path(safe_key).parts:
            raise DomainError("key invalida", rule_id="RN-112")
        dest = self.root / safe_key
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        return dest.as_uri()

    def exists(self, uri: str) -> bool:
        try:
            return self.resolve(uri).is_file()
        except (NotFoundError, DomainError, ValueError, OSError):
            return False

    def resolve(self, uri: str) -> Path:
        parsed = urlparse(uri)
        if parsed.scheme not in ("file", ""):
            raise DomainError(f"URI nao suportada neste adapter: {uri}")
        if parsed.scheme == "file":
            path = Path(unquote(parsed.path))
        else:
            path = Path(uri)
        path = path.resolve()
        try:
            path.relative_to(self.root)
        except ValueError as exc:
            raise DomainError("URI fora do root do ArtifactStore", rule_id="RN-112") from exc
        if not path.exists():
            raise NotFoundError(f"artefacto inexistente: {uri}")
        return path
