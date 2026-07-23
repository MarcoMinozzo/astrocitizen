"""AC-198: glossario sync + lookup."""

from __future__ import annotations

import json
from pathlib import Path

from astrocitizen.adapters.sqlite import HybridRetriever, SqliteArchive
from astrocitizen.knowledge.glossary import (
    get_entry,
    list_entries,
    search_entries,
    sync_glossary_chunks,
)
from astrocitizen.knowledge.mcp_tools import TOOL_KB_GET_GLOSSARY, KbMcpServer
from astrocitizen.knowledge.models import KnowledgeDocument


def _mini_kb(tmp_path: Path) -> Path:
    kb = tmp_path / "knowledge-base"
    (kb / "chunks" / "v1").mkdir(parents=True)
    (kb / "catalog.json").write_text(
        json.dumps({"schema_version": 1, "sources": [], "updated_utc": "2026-07-23"}),
        encoding="utf-8",
    )
    (kb / "glossary.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "entries": [
                    {
                        "term_id": "spectrum-report",
                        "term": "spectrum_report",
                        "aliases": ["AC-106"],
                        "lang": "pt",
                        "definition": "Interpretacao espectral deterministica.",
                        "topics": ["spectrum"],
                        "po_ids": ["PO-B01"],
                        "networks": ["bess"],
                    },
                    {
                        "term_id": "po-g01",
                        "term": "PO-G01",
                        "aliases": ["duplas"],
                        "lang": "pt",
                        "definition": "Medidas de duplas WDS.",
                        "topics": ["programs"],
                        "po_ids": ["PO-G01"],
                        "networks": ["wds"],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    return kb


def test_glossary_lookup_and_search(tmp_path: Path) -> None:
    kb = _mini_kb(tmp_path)
    hit = get_entry("AC-106", kb_root=kb)
    assert hit is not None
    assert hit.term_id == "spectrum-report"
    hits = search_entries("duplas", kb_root=kb)
    assert any(e.term_id == "po-g01" for e in hits)
    assert len(list_entries(kb)) == 2


def test_glossary_sync_chunks(tmp_path: Path) -> None:
    kb = _mini_kb(tmp_path)
    report = sync_glossary_chunks(kb_root=kb)
    assert report.n_chunks_written == 2
    files = list((kb / "chunks" / "v1").glob("glossary-*.md"))
    assert len(files) == 2
    catalog = json.loads((kb / "catalog.json").read_text(encoding="utf-8"))
    assert any(s["source_id"] == "glossary" for s in catalog["sources"])


def test_mcp_kb_get_glossary(tmp_path: Path) -> None:
    # uses real default glossary if present; also works with empty archive
    archive = SqliteArchive(tmp_path / "g.sqlite3")
    archive.migrate()
    archive.upsert_knowledge_document(
        KnowledgeDocument(
            id="docs-x",
            source_id="docs-x",
            path="x.md",
            title="X",
            trust_tier="T3",
            status="ingested",
        )
    )
    server = KbMcpServer(HybridRetriever(archive))
    # project glossary.json should exist after AC-198 seed
    from astrocitizen.knowledge.scaffold import default_kb_root

    if (default_kb_root() / "glossary.json").is_file():
        got = server.call_tool(TOOL_KB_GET_GLOSSARY, {"term": "AAVSO"})
        assert got["ok"]
        assert got["entry"]["term"] == "AAVSO"
    listed = server.call_tool(TOOL_KB_GET_GLOSSARY, {"limit": 5})
    assert listed["ok"]
    assert "entries" in listed
    archive.close()
