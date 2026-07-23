"""Glossario astro/redes/PO → lookup + sync chunks (AC-198)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from astrocitizen.knowledge.frontmatter import render_chunk_markdown
from astrocitizen.knowledge.scaffold import default_kb_root, load_json
from astrocitizen.shared.timeutil import utc_now_iso


@dataclass
class GlossaryEntry:
    term_id: str
    term: str
    definition: str
    aliases: list[str] = field(default_factory=list)
    lang: str = "pt"
    topics: list[str] = field(default_factory=list)
    po_ids: list[str] = field(default_factory=list)
    networks: list[str] = field(default_factory=list)


@dataclass
class GlossarySyncReport:
    n_entries: int
    n_chunks_written: int
    glossary_path: str
    built_utc: str


def glossary_path(kb_root: Path | None = None) -> Path:
    return (kb_root or default_kb_root()) / "glossary.json"


def load_glossary(kb_root: Path | None = None) -> dict[str, Any]:
    path = glossary_path(kb_root)
    if not path.is_file():
        return {"schema_version": 1, "entries": []}
    return load_json(path)


def list_entries(kb_root: Path | None = None) -> list[GlossaryEntry]:
    raw = load_glossary(kb_root)
    out: list[GlossaryEntry] = []
    for item in raw.get("entries") or []:
        if not isinstance(item, dict):
            continue
        tid = str(item.get("term_id") or "").strip()
        term = str(item.get("term") or "").strip()
        definition = str(item.get("definition") or "").strip()
        if not tid or not term or not definition:
            continue
        out.append(
            GlossaryEntry(
                term_id=tid,
                term=term,
                definition=definition,
                aliases=[str(a) for a in (item.get("aliases") or [])],
                lang=str(item.get("lang") or "pt"),
                topics=[str(t) for t in (item.get("topics") or [])],
                po_ids=[str(p) for p in (item.get("po_ids") or [])],
                networks=[str(n) for n in (item.get("networks") or [])],
            )
        )
    return out


def get_entry(
    query: str,
    *,
    kb_root: Path | None = None,
    lang: str | None = None,
) -> GlossaryEntry | None:
    """Lookup exact/alias (casefold); opcional filtro lang."""
    q = (query or "").strip()
    if not q:
        return None
    qn = q.casefold()
    for e in list_entries(kb_root):
        if lang and e.lang != lang:
            continue
        names = [e.term, e.term_id, *e.aliases]
        if any(n.casefold() == qn for n in names if n):
            return e
    return None


def search_entries(
    query: str,
    *,
    kb_root: Path | None = None,
    limit: int = 20,
    topic: str | None = None,
    network: str | None = None,
    po_id: str | None = None,
) -> list[GlossaryEntry]:
    q = (query or "").strip().casefold()
    hits: list[GlossaryEntry] = []
    for e in list_entries(kb_root):
        if topic and topic not in e.topics:
            continue
        if network and network not in e.networks:
            continue
        if po_id and po_id not in e.po_ids:
            continue
        blob = " ".join([e.term, e.term_id, e.definition, *e.aliases]).casefold()
        if q and q not in blob:
            continue
        hits.append(e)
        if len(hits) >= limit:
            break
    return hits


def sync_glossary_chunks(
    *,
    kb_root: Path | None = None,
    corpus_version: str = "0.1.0-kb1",
) -> GlossarySyncReport:
    """Escreve um chunk markdown por entrada em chunks/v1/glossary-*.md."""
    kb = kb_root or default_kb_root()
    entries = list_entries(kb)
    chunks_dir = kb / "chunks" / "v1"
    chunks_dir.mkdir(parents=True, exist_ok=True)
    for old in chunks_dir.glob("glossary-*.md"):
        old.unlink(missing_ok=True)
    written = 0
    for e in entries:
        chunk_id = f"glossary-{_slug(e.term_id)}"
        body = _entry_body(e)
        meta = {
            "chunk_id": chunk_id,
            "source_id": "glossary",
            "path": "knowledge-base/glossary.json",
            "title": e.term,
            "trust_tier": "T3",
            "lang": e.lang,
            "topics": list(e.topics) + ["glossary"],
            "po_id": e.po_ids[0] if e.po_ids else None,
            "network": e.networks[0] if e.networks else None,
            "pipeline_stage": "help",
            "token_estimate": max(1, len(body.split())),
            "chunk_hash": f"sha256:glossary:{e.term_id}",
            "corpus_version": corpus_version,
        }
        (chunks_dir / f"{chunk_id}.md").write_text(
            render_chunk_markdown(meta, body), encoding="utf-8"
        )
        written += 1
    _ensure_catalog_glossary(kb)
    built = utc_now_iso()
    return GlossarySyncReport(
        n_entries=len(entries),
        n_chunks_written=written,
        glossary_path=str(glossary_path(kb)),
        built_utc=built,
    )


def entry_to_dict(e: GlossaryEntry) -> dict[str, Any]:
    return {
        "term_id": e.term_id,
        "term": e.term,
        "aliases": list(e.aliases),
        "lang": e.lang,
        "definition": e.definition,
        "topics": list(e.topics),
        "po_ids": list(e.po_ids),
        "networks": list(e.networks),
    }


def _entry_body(e: GlossaryEntry) -> str:
    lines = [
        f"# {e.term}",
        "",
        e.definition,
        "",
    ]
    if e.aliases:
        lines.append("**Aliases:** " + ", ".join(e.aliases))
    if e.po_ids:
        lines.append("**PO:** " + ", ".join(e.po_ids))
    if e.networks:
        lines.append("**Networks:** " + ", ".join(e.networks))
    if e.topics:
        lines.append("**Topics:** " + ", ".join(e.topics))
    return "\n".join(lines).rstrip() + "\n"


def _slug(term_id: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9\-]+", "-", term_id).strip("-").lower()
    return s or "term"


def _ensure_catalog_glossary(kb: Path) -> None:
    path = kb / "catalog.json"
    if not path.is_file():
        return
    catalog = load_json(path)
    sources = list(catalog.get("sources") or [])
    if any(isinstance(s, dict) and s.get("source_id") == "glossary" for s in sources):
        for s in sources:
            if isinstance(s, dict) and s.get("source_id") == "glossary":
                s["status"] = "ingested"
                s["path"] = "knowledge-base/glossary.json"
        catalog["sources"] = sources
    else:
        sources.append(
            {
                "source_id": "glossary",
                "path": "knowledge-base/glossary.json",
                "title": "Glossario astro / redes / PO",
                "trust_tier": "T3",
                "license_id": "project-docs",
                "lang": "pt",
                "topics": ["glossary", "product"],
                "status": "ingested",
            }
        )
        catalog["sources"] = sources
    catalog["updated_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
