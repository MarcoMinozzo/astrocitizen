"""Adapter: lancar ferramentas externas de imagem (Siril, DS9, SO)."""

from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

from astrocitizen.shared.errors import DomainError


DEFAULT_TOOL_COMMANDS: dict[str, str] = {
    "system": "",  # QDesktopServices / xdg-open
    "ds9": "ds9 %f",
    "siril": "siril %f",
    "astap": "astap %f",
}


def load_image_tool_commands() -> dict[str, str]:
    """Preferencias Qt: image_tool.<id> = command template com %f."""
    out = dict(DEFAULT_TOOL_COMMANDS)
    try:
        from PySide6.QtCore import QSettings
    except ImportError:
        return out
    settings = QSettings("AstroCitizen", "desktop")
    for tool_id in DEFAULT_TOOL_COMMANDS:
        key = f"image_tool/{tool_id}"
        raw = settings.value(key, "")
        text = str(raw or "").strip()
        if text:
            out[tool_id] = text
    return out


def save_image_tool_command(tool_id: str, command: str) -> None:
    try:
        from PySide6.QtCore import QSettings
    except ImportError:
        return
    settings = QSettings("AstroCitizen", "desktop")
    settings.setValue(f"image_tool/{tool_id}", (command or "").strip())


def build_command(template: str, path: Path) -> list[str]:
    path = Path(path)
    if not template.strip():
        return []
    # Replace %f before shlex so spaces in path stay one token if quoted in template
    rendered = template.replace("%f", str(path))
    return shlex.split(rendered)


class ExternalImageToolLauncher:
    """ImageToolPort: subprocess ou abrir com o SO."""

    def __init__(self, commands: dict[str, str] | None = None) -> None:
        self.commands = commands or load_image_tool_commands()

    def launch(self, path: Path, *, tool_id: str = "system") -> bool:
        path = Path(path)
        if not path.exists():
            raise DomainError(f"ficheiro nao encontrado: {path}")
        tool = (tool_id or "system").strip().lower()
        template = self.commands.get(tool, "")
        if tool == "system" or not template.strip():
            return self._open_system(path)
        argv = build_command(template, path)
        if not argv:
            return self._open_system(path)
        try:
            subprocess.Popen(  # noqa: S603 - user-configured tool
                argv,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            return True
        except OSError as exc:
            raise DomainError(f"falha ao lancar {tool}: {exc}") from exc

    def _open_system(self, path: Path) -> bool:
        try:
            from PySide6.QtCore import QUrl
            from PySide6.QtGui import QDesktopServices

            return bool(QDesktopServices.openUrl(QUrl.fromLocalFile(str(path))))
        except ImportError:
            try:
                subprocess.Popen(  # noqa: S603
                    ["xdg-open", str(path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                return True
            except OSError as exc:
                raise DomainError(f"falha xdg-open: {exc}") from exc
