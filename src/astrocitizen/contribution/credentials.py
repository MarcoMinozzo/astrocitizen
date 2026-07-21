"""Credenciais locais de redes (AC-142) - fora do SQLite."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from astrocitizen.shared.paths import default_data_dir


def default_credentials_path() -> Path:
    return default_data_dir() / "credentials.json"


class LocalCredentialsStore:
    """JSON local com chaves por rede (aavso / mpc / tns)."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path) if path else default_credentials_path()

    def load(self) -> dict[str, Any]:
        if not self.path.is_file():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(data, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )

    def get_network(self, network: str) -> dict[str, Any]:
        return dict(self.load().get(network) or {})

    def set_network(self, network: str, values: dict[str, Any]) -> None:
        data = self.load()
        cur = dict(data.get(network) or {})
        cur.update({k: v for k, v in values.items() if v is not None})
        data[network] = cur
        self.save(data)
