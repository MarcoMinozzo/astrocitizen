"""Testes CLI S1."""

from __future__ import annotations

from pathlib import Path

from astrocitizen.cli import main


def test_cli_init_db_and_site_program(tmp_path: Path, capsys) -> None:
    db = tmp_path / "ac.sqlite3"
    artifacts = tmp_path / "artifacts"
    assert main(["init-db", "--db", str(db), "--artifacts", str(artifacts)]) == 0
    out = capsys.readouterr().out
    assert "templates_seeded=" in out
    assert artifacts.is_dir()

    assert (
        main(
            [
                "site",
                "add",
                "--db",
                str(db),
                "--name",
                "Casa",
                "--lat",
                "-29.7",
                "--lon",
                "-51.1",
                "--default",
            ]
        )
        == 0
    )
    assert main(["site", "list", "--db", str(db)]) == 0
    assert "Casa" in capsys.readouterr().out

    assert (
        main(
            [
                "equipment",
                "add",
                "--db",
                str(db),
                "--type",
                "camera",
                "--name",
                "ST-7",
                "--backend",
                "sim",
            ]
        )
        == 0
    )
    assert main(["program", "templates", "--db", str(db), "--class", "A"]) == 0
    tmpl_out = capsys.readouterr().out
    assert "PO-A01" in tmpl_out

    assert (
        main(
            [
                "program",
                "create",
                "--db",
                str(db),
                "--template",
                "PO-A01",
                "--name",
                "Vars",
            ]
        )
        == 0
    )
    assert main(["program", "list", "--db", str(db)]) == 0
    assert "Vars" in capsys.readouterr().out
