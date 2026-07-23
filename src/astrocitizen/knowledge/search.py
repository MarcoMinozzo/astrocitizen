"""Pesquisa lexical FTS5 da KB (AC-193)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from astrocitizen.knowledge.scaffold import default_kb_root, load_json
from astrocitizen.shared.timeutil import utc_now_iso

_TOKEN_RE = re.compile(r"[A-Za-z0-9_\u00C0-\u024F\-]+", re.UNICODE)
_NON_ASCII_RE = re.compile(r"[^\x00-\x7f]+")
_STOP = frozenset(
    {
        "a",
        "as",
        "o",
        "os",
        "de",
        "da",
        "do",
        "das",
        "dos",
        "e",
        "em",
        "um",
        "uma",
        "para",
        "por",
        "com",
        "ou",
        "que",
        "se",
        "na",
        "no",
        "nas",
        "nos",
        "ao",
        "aos",
        "the",
        "of",
        "and",
        "to",
        "in",
        "is",
        "are",
        "what",
        "quais",
        "sao",
        "são",
    }
)


def fold_corrupt_accents(text: str) -> str:
    """Normaliza texto para FTS: remove acentos e bytes corruptos (WORKFLOWS.md).

    Em WORKFLOWS.md, 0xff (U+00FF ÿ) substituiu acentos PT. NFKD transforma ÿ→y,
    o que impede 'navegacao' de fazer match; por isso apagamos U+00FF antes.
    """
    if not text:
        return ""
    import unicodedata

    cleaned = text.replace("\ufffd", "").replace("\u00ff", "").replace("\u00df", "")
    norm = unicodedata.normalize("NFKD", cleaned)
    ascii_ish = "".join(ch for ch in norm if not unicodedata.combining(ch))
    return _NON_ASCII_RE.sub("", ascii_ish)


def build_fts_query(text: str) -> str:
    """Converte texto livre em MATCH FTS5 (OR de tokens; prefixo para recall)."""
    raw = fold_corrupt_accents((text or "").strip())
    if not raw:
        return ""
    tokens: list[str] = []
    for m in _TOKEN_RE.finditer(raw):
        tok = m.group(0)
        if len(tok) < 2:
            continue
        if tok.lower() in _STOP:
            continue
        safe = tok.replace('"', "")
        if not safe:
            continue
        tokens.append(f'"{safe}"*')
    if not tokens:
        esc = raw.replace('"', '""')
        return f'"{esc}"'
    return " OR ".join(tokens)


@dataclass
class SearchHit:
    chunk_id: str
    source_id: str
    trust_tier: str
    title: str | None
    score: float
    snippet: str
    path: str | None = None
    lang: str | None = None
    po_id: str | None = None
    network: str | None = None
    topics: list[str] = field(default_factory=list)
    chunk_hash: str | None = None


@dataclass
class FtsIndexReport:
    n_rows: int
    built_utc: str
    engine: str = "sqlite-fts5"
    table: str = "knowledge_chunks_fts"
    tokenizer: str = "unicode61"


def rebuild_fts_index(
    archive: Any,
    *,
    kb_root: Path | None = None,
    update_manifest: bool = True,
) -> FtsIndexReport:
    """Rebuild FTS + opcionalmente actualiza manifest.index.fts (fase KB-2)."""
    n = int(archive.rebuild_knowledge_fts())
    built = utc_now_iso()
    report = FtsIndexReport(n_rows=n, built_utc=built)
    if update_manifest:
        _update_manifest_fts(kb_root or default_kb_root(), report)
    return report


def search_knowledge(
    archive: Any,
    query: str,
    *,
    limit: int = 10,
    trust_tier: str | None = None,
    source_id: str | None = None,
    lang: str | None = None,
    po_id: str | None = None,
    network: str | None = None,
) -> list[SearchHit]:
    rows = archive.search_knowledge_chunks(
        query,
        limit=limit,
        trust_tier=trust_tier,
        source_id=source_id,
        lang=lang,
        po_id=po_id,
        network=network,
    )
    hits: list[SearchHit] = []
    for r in rows:
        hits.append(
            SearchHit(
                chunk_id=str(r["chunk_id"]),
                source_id=str(r["source_id"]),
                trust_tier=str(r["trust_tier"]),
                title=r.get("title"),
                score=float(r.get("score") or 0.0),
                snippet=str(r.get("snippet") or ""),
                path=r.get("path"),
                lang=r.get("lang"),
                po_id=r.get("po_id"),
                network=r.get("network"),
                topics=list(r.get("topics") or []),
                chunk_hash=r.get("chunk_hash"),
            )
        )
    return hits


def _utc_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _update_manifest_fts(kb_root: Path, report: FtsIndexReport) -> None:
    path = Path(kb_root) / "manifest.json"
    if not path.is_file():
        return
    manifest = load_json(path)
    index = dict(manifest.get("index") or {})
    index["fts"] = {
        "engine": report.engine,
        "table": report.table,
        "tokenizer": report.tokenizer,
        "built_utc": report.built_utc,
        "n_rows": report.n_rows,
    }
    # embeddings permanece como estava (null ate AC-195)
    if "embeddings" not in index:
        index["embeddings"] = None
    manifest["index"] = index
    manifest["phase"] = "KB-2"
    manifest["updated_utc"] = _utc_date()
    path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
