from __future__ import annotations

from astrocitizen.cli import main


def test_cli_version(capsys) -> None:
    assert main(["version"]) == 0
    assert capsys.readouterr().out.strip() == "0.0.1"


def test_cli_modules(capsys) -> None:
    assert main(["modules"]) == 0
    out = capsys.readouterr().out
    assert "planning" in out
    assert "observatory" in out


def test_cli_help_without_command() -> None:
    assert main([]) == 0
