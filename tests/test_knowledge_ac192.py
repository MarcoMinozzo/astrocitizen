"""AC-192: ingest T3 docs/atlas → chunks."""

from __future__ import annotations

import json
from pathlib import Path

from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.knowledge.chunking import chunk_markdown, estimate_tokens
from astrocitizen.knowledge.frontmatter import render_chunk_markdown
from astrocitizen.knowledge.ingest import _read_text, ingest_sources


def test_read_text_latin1_fallback(tmp_path: Path) -> None:
    # WORKFLOWS.md-like corruption: 0xff where accents belonged
    path = tmp_path / "broken.md"
    path.write_bytes(b"# Workflows do usu\xffrio\n\n## Secao\n\ntexto")
    text = _read_text(path)
    assert "Workflows" in text
    assert "Secao" in text
    assert "\xff" in text or "\u00ff" in text


def test_estimate_and_chunk_sizes() -> None:
    para = " ".join(["palavra"] * 80)
    sections = "\n\n".join(
        [f"## Secao {i}\n\n{para}\n\n{para}" for i in range(1, 8)]
    )
    chunks = chunk_markdown(sections, min_tokens=100, max_tokens=400)
    assert len(chunks) >= 3
    for ch in chunks:
        assert ch.token_estimate >= 50
        assert ch.token_estimate <= 500


def test_render_chunk_frontmatter() -> None:
    text = render_chunk_markdown(
        {
            "chunk_id": "docs-workflows-001",
            "source_id": "docs-workflows",
            "path": "docs/WORKFLOWS.md",
            "title": "Modo Contribuir",
            "trust_tier": "T3",
            "lang": "pt",
            "topics": ["workflows"],
            "po_id": None,
            "network": None,
            "pipeline_stage": "help",
            "token_estimate": 120,
            "chunk_hash": "sha256:abc",
            "corpus_version": "0.1.0-kb1",
        },
        "Body text here.",
    )
    assert text.startswith("---\n")
    assert 'chunk_id: "docs-workflows-001"' in text or "chunk_id: docs-workflows-001" in text
    assert "Body text here." in text


def test_ingest_t3_tmp_kb(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    docs = repo / "docs"
    docs.mkdir(parents=True)
    # synthetic T3-sized docs
    body = "\n\n".join(
        [f"## Topic {i}\n\n" + ("conteudo observacional " * 60) for i in range(1, 12)]
    )
    (docs / "WORKFLOWS.md").write_text("# WF\n\n" + body, encoding="utf-8")
    (docs / "PROGRAMAS_OBSERVACIONAIS.md").write_text(
        "# PO\n\n" + body, encoding="utf-8"
    )
    kb = repo / "knowledge-base"
    (kb / "chunks" / "v1").mkdir(parents=True)
    (kb / "processed").mkdir(parents=True)
    catalog = {
        "schema_version": 1,
        "updated_utc": "2026-07-23",
        "sources": [
            {
                "source_id": "docs-workflows",
                "path": "docs/WORKFLOWS.md",
                "title": "WF",
                "trust_tier": "T3",
                "license_id": "project-docs",
                "lang": "pt",
                "topics": ["workflows"],
                "status": "planned_ingest",
            },
            {
                "source_id": "docs-programas",
                "path": "docs/PROGRAMAS_OBSERVACIONAIS.md",
                "title": "PO",
                "trust_tier": "T3",
                "license_id": "project-docs",
                "lang": "pt",
                "topics": ["programs"],
                "status": "planned_ingest",
            },
            {
                "source_id": "docs-lit",
                "path": "docs/LIT.md",
                "title": "Lit",
                "trust_tier": "T5",
                "license_id": "project-docs",
                "lang": "pt",
                "topics": ["literature"],
                "status": "planned_ingest",
            },
        ],
    }
    (kb / "catalog.json").write_text(
        json.dumps(catalog, indent=2), encoding="utf-8"
    )
    (kb / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "corpus_version": "0.0.0-kb0",
                "phase": "KB-0",
                "n_sources": 0,
                "n_chunks": 0,
                "ingest": {"status": "not_started", "notes": ""},
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    dry = ingest_sources(
        archive=None,
        kb_root=kb,
        repo_root=repo,
        trust_tiers=("T3",),
        dry_run=True,
        write_files=True,
        write_db=False,
        min_tokens=80,
        max_tokens=350,
    )
    assert dry.n_sources == 2
    assert dry.n_chunks >= 4
    assert not list((kb / "chunks" / "v1").glob("*.md"))

    archive = SqliteArchive(tmp_path / "kb.sqlite3")
    archive.migrate()
    report = ingest_sources(
        archive=archive,
        kb_root=kb,
        repo_root=repo,
        trust_tiers=("T3",),
        write_files=True,
        write_db=True,
        min_tokens=80,
        max_tokens=350,
        corpus_version="0.1.0-kb1",
    )
    assert report.ok
    assert report.n_chunks >= 4
    assert (kb / "processed" / "docs-workflows.md").is_file()
    chunk_files = list((kb / "chunks" / "v1").glob("docs-workflows-*.md"))
    assert chunk_files
    assert archive.list_knowledge_documents(status="ingested")
    assert len(archive.list_knowledge_chunks(source_id="docs-workflows")) >= 1
    manifest = json.loads((kb / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["phase"] == "KB-1"
    assert manifest["n_chunks"] == report.n_chunks
    catalog2 = json.loads((kb / "catalog.json").read_text(encoding="utf-8"))
    statuses = {
        s["source_id"]: s["status"] for s in catalog2["sources"] if s["trust_tier"] == "T3"
    }
    assert statuses["docs-workflows"] == "ingested"
    assert statuses["docs-programas"] == "ingested"
    # T5 untouched
    assert catalog2["sources"][2]["status"] == "planned_ingest"
    archive.close()


def test_token_estimate_positive() -> None:
    assert estimate_tokens("um dois tres") >= 1
