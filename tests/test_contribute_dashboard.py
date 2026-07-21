"""Testes helpers do painel Contribute."""

from __future__ import annotations

from types import SimpleNamespace

from astrocitizen.desktop.contribute import credentials_status_lines, submission_table_rows


def test_submission_table_rows() -> None:
    subs = [
        SimpleNamespace(
            created_at="2026-07-21T12:00:00Z",
            network="aavso",
            status="draft",
            id="abcdef12-3333-4444-5555-666677778888",
            artifact_uri="file:///tmp/a.txt",
        )
    ]
    rows = submission_table_rows(subs)
    assert rows[0][1] == "aavso"
    assert rows[0][3] == "abcdef12"


def test_credentials_status_lines() -> None:
    class Store:
        def load(self):
            return {"aavso": {"obscode": "XYZ"}, "mpc": {}, "tns": {"api_key": "secret"}}

    lines = credentials_status_lines(Store())
    assert any("obscode=XYZ" in x for x in lines)
    assert any("api_key=***" in x for x in lines)
    assert any("mpc:" in x for x in lines)
