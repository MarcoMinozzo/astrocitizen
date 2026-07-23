"""Ingest offline T3 docs/atlas → processed + chunks + SQLite (AC-192)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from astrocitizen.knowledge.chunking import chunk_markdown
from astrocitizen.knowledge.frontmatter import render_chunk_markdown
from astrocitizen.knowledge.models import KnowledgeChunk, KnowledgeDocument
from astrocitizen.knowledge.scaffold import default_kb_root, load_json
from astrocitizen.shared.timeutil import utc_now_iso


def _sha256_text(text: str) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _utc_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


@dataclass
class IngestReport:
    corpus_version: str
    n_sources: int = 0
    n_chunks: int = 0
    sources: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors and self.n_chunks > 0


def load_catalog(kb_root: Path) -> dict[str, Any]:
    return load_json(kb_root / "catalog.json")


def select_sources(
    catalog: dict[str, Any],
    *,
    trust_tiers: tuple[str, ...] = ("T3",),
    source_id: str | None = None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for src in catalog.get("sources") or []:
        if not isinstance(src, dict):
            continue
        if source_id and src.get("source_id") != source_id:
            continue
        if trust_tiers and src.get("trust_tier") not in trust_tiers:
            continue
        out.append(src)
    return out


def _read_text(path: Path) -> str:
    """Lê texto; UTF-8 preferido. Ficheiros com bytes corruptos (ex. 0xff) → latin-1.

    Não tenta UTF-16 sem BOM: qualquer ficheiro de comprimento par “decodifica”
    e produz lixo (caso WORKFLOWS.md).
    """
    raw = path.read_bytes()
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16")
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        # Ex.: docs/WORKFLOWS.md com 0xff no lugar de acentos PT
        return raw.decode("latin-1")


def ingest_sources(
    *,
    archive: Any | None = None,
    kb_root: Path | None = None,
    repo_root: Path | None = None,
    trust_tiers: tuple[str, ...] = ("T3",),
    source_id: str | None = None,
    write_files: bool = True,
    write_db: bool = True,
    dry_run: bool = False,
    corpus_version: str = "0.1.0-kb1",
    min_tokens: int = 200,
    max_tokens: int = 700,
) -> IngestReport:
    """Ingere fontes do catalogo para ficheiros KB e/ou SQLite."""
    kb = Path(kb_root) if kb_root is not None else default_kb_root()
    root = Path(repo_root) if repo_root is not None else kb.parent
    report = IngestReport(corpus_version=corpus_version)
    catalog = load_catalog(kb)
    sources = select_sources(
        catalog, trust_tiers=trust_tiers, source_id=source_id
    )
    if not sources:
        report.errors.append("nenhuma fonte selecionada para ingest")
        return report

    processed_dir = kb / "processed"
    chunks_dir = kb / "chunks" / "v1"
    if write_files and not dry_run:
        processed_dir.mkdir(parents=True, exist_ok=True)
        chunks_dir.mkdir(parents=True, exist_ok=True)

    ingested_ids: set[str] = set()
    total_chunks = 0

    for src in sources:
        sid = str(src.get("source_id") or "").strip()
        rel = str(src.get("path") or "").strip()
        src_path = root / rel
        if not sid or not rel:
            report.errors.append(f"fonte invalida: {src}")
            continue
        if not src_path.is_file():
            report.errors.append(f"{sid}: ficheiro em falta: {rel}")
            continue
        try:
            text = _read_text(src_path)
        except OSError as exc:
            report.errors.append(f"{sid}: leitura falhou: {exc}")
            continue

        content_hash = _sha256_text(text)
        raw_chunks = chunk_markdown(
            text, min_tokens=min_tokens, max_tokens=max_tokens
        )
        if not raw_chunks:
            report.errors.append(f"{sid}: nenhum chunk gerado")
            continue

        if write_files and not dry_run:
            (processed_dir / f"{sid}.md").write_text(text, encoding="utf-8")
            for old in chunks_dir.glob(f"{sid}-*.md"):
                old.unlink(missing_ok=True)

        if write_db and archive is not None and not dry_run:
            # hard-replace previous chunks for this source (stable chunk_ids)
            archive._conn.execute(
                "DELETE FROM knowledge_chunks WHERE source_id = ?", (sid,)
            )
            archive._conn.commit()
            archive.upsert_knowledge_document(
                KnowledgeDocument(
                    id=sid,
                    source_id=sid,
                    path=rel,
                    title=str(src.get("title") or sid),
                    trust_tier=str(src.get("trust_tier") or "T3"),
                    license_id=src.get("license_id"),
                    lang=src.get("lang") or "pt",
                    topics=list(src.get("topics") or []),
                    networks=list(src.get("networks") or []),
                    content_hash=content_hash,
                    corpus_version=corpus_version,
                    status="ingested",
                )
            )

        for i, raw in enumerate(raw_chunks, start=1):
            chunk_id = f"{sid}-{i:03d}"
            chunk_hash = _sha256_text(raw.body)
            meta = {
                "chunk_id": chunk_id,
                "source_id": sid,
                "path": rel,
                "title": raw.title,
                "trust_tier": str(src.get("trust_tier") or "T3"),
                "lang": src.get("lang") or "pt",
                "topics": list(src.get("topics") or []),
                "po_id": raw.po_id,
                "network": raw.network,
                "pipeline_stage": "help",
                "token_estimate": raw.token_estimate,
                "chunk_hash": chunk_hash,
                "corpus_version": corpus_version,
            }
            if write_files and not dry_run:
                out_path = chunks_dir / f"{chunk_id}.md"
                out_path.write_text(
                    render_chunk_markdown(meta, raw.body), encoding="utf-8"
                )
            if write_db and archive is not None and not dry_run:
                archive.upsert_knowledge_chunk(
                    KnowledgeChunk(
                        id=chunk_id,
                        document_id=sid,
                        source_id=sid,
                        body=raw.body,
                        trust_tier=str(src.get("trust_tier") or "T3"),
                        chunk_hash=chunk_hash,
                        path=rel,
                        title=raw.title,
                        lang=src.get("lang") or "pt",
                        topics=list(src.get("topics") or []),
                        po_id=raw.po_id,
                        network=raw.network,
                        pipeline_stage="help",
                        token_estimate=raw.token_estimate,
                        corpus_version=corpus_version,
                        sort_order=i,
                    )
                )
            total_chunks += 1

        ingested_ids.add(sid)
        report.sources.append(
            {
                "source_id": sid,
                "path": rel,
                "n_chunks": len(raw_chunks),
                "content_hash": content_hash,
            }
        )
        report.n_sources += 1

    report.n_chunks = total_chunks

    if dry_run:
        return report

    if write_files:
        _update_catalog_status(kb, ingested_ids)
        _update_manifest(
            kb,
            corpus_version=corpus_version,
            n_sources=report.n_sources,
            n_chunks=report.n_chunks,
        )

    return report


def _update_catalog_status(kb: Path, ingested_ids: set[str]) -> None:
    path = kb / "catalog.json"
    catalog = load_json(path)
    today = _utc_date()
    for src in catalog.get("sources") or []:
        if isinstance(src, dict) and src.get("source_id") in ingested_ids:
            src["status"] = "ingested"
    catalog["updated_utc"] = today
    path.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _update_manifest(
    kb: Path,
    *,
    corpus_version: str,
    n_sources: int,
    n_chunks: int,
) -> None:
    path = kb / "manifest.json"
    manifest = load_json(path)
    today = _utc_date()
    manifest["corpus_version"] = corpus_version
    manifest["phase"] = "KB-1"
    manifest["updated_utc"] = today
    manifest["n_sources"] = n_sources
    manifest["n_chunks"] = n_chunks
    ingest = dict(manifest.get("ingest") or {})
    ingest["status"] = "completed" if n_chunks else "failed"
    ingest["notes"] = f"AC-192 offline ingest {utc_now_iso()}"
    manifest["ingest"] = ingest
    path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
