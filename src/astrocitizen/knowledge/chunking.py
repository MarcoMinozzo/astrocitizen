"""Chunking de markdown para KB (AC-192) — alvo 300-800 tokens."""

from __future__ import annotations

import re
from dataclasses import dataclass


def estimate_tokens(text: str) -> int:
    words = len((text or "").split())
    return max(1, (words * 4) // 3) if words else 1


@dataclass
class RawSection:
    title: str
    level: int
    body: str


@dataclass
class RawChunk:
    title: str
    body: str
    token_estimate: int
    network: str | None = None
    po_id: str | None = None


_HEADING_RE = re.compile(r"^(#{2,4})\s+(.+?)\s*$", re.MULTILINE)
_PO_RE = re.compile(r"\bPO-[A-Z]\d{2}\b")
_NETWORK_KEYS = (
    "aavso",
    "mpc",
    "bess",
    "exoclock",
    "iota",
    "tns",
    "wds",
    "cobs",
    "solar",
)


def _detect_network(title: str, body: str) -> str | None:
    blob = f"{title}\n{body}".lower()
    for key in _NETWORK_KEYS:
        if re.search(rf"\b{re.escape(key)}\b", blob):
            return key
    return None


def _detect_po(title: str, body: str) -> str | None:
    m = _PO_RE.search(f"{title}\n{body}")
    return m.group(0) if m else None


def split_markdown_sections(text: str) -> list[RawSection]:
    """Parte por headings ## / ### / ####; prefacio fica level 1."""
    text = (text or "").replace("\r\n", "\n")
    matches = list(_HEADING_RE.finditer(text))
    if not matches:
        body = text.strip()
        return [RawSection(title="Document", level=1, body=body)] if body else []

    sections: list[RawSection] = []
    preface = text[: matches[0].start()].strip()
    if preface:
        sections.append(RawSection(title="Introduction", level=1, body=preface))
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        sections.append(
            RawSection(title=m.group(2).strip(), level=len(m.group(1)), body=body)
        )
    return sections


def _split_oversized(title: str, body: str, *, max_tokens: int) -> list[tuple[str, str]]:
    if estimate_tokens(body) <= max_tokens:
        return [(title, body)]
    paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    if len(paras) <= 1:
        # hard split by lines
        lines = body.splitlines()
        mid = max(1, len(lines) // 2)
        left = "\n".join(lines[:mid]).strip()
        right = "\n".join(lines[mid:]).strip()
        out: list[tuple[str, str]] = []
        if left:
            out.extend(_split_oversized(f"{title} (1)", left, max_tokens=max_tokens))
        if right:
            out.extend(_split_oversized(f"{title} (2)", right, max_tokens=max_tokens))
        return out or [(title, body)]
    chunks: list[tuple[str, str]] = []
    buf: list[str] = []
    part = 1
    for p in paras:
        trial = ("\n\n".join(buf + [p])).strip()
        if buf and estimate_tokens(trial) > max_tokens:
            chunks.append((f"{title} ({part})", "\n\n".join(buf).strip()))
            part += 1
            buf = [p]
        else:
            buf.append(p)
    if buf:
        chunks.append((f"{title} ({part})" if part > 1 else title, "\n\n".join(buf).strip()))
    return chunks


def chunk_markdown(
    text: str,
    *,
    min_tokens: int = 200,
    max_tokens: int = 700,
) -> list[RawChunk]:
    """Agrupa secoes ate ~min_tokens; parte se > max_tokens (alvo tipico 200-700)."""
    sections = split_markdown_sections(text)
    if not sections:
        return []

    merged: list[tuple[str, str]] = []
    buf_title = ""
    buf_parts: list[str] = []

    def flush() -> None:
        nonlocal buf_title, buf_parts
        if not buf_parts:
            return
        body = "\n\n".join(buf_parts).strip()
        title = buf_title or "Section"
        for t, b in _split_oversized(title, body, max_tokens=max_tokens):
            if b.strip():
                merged.append((t, b.strip()))
        buf_title = ""
        buf_parts = []

    for sec in sections:
        piece = f"## {sec.title}\n\n{sec.body}".strip() if sec.body else f"## {sec.title}"
        if not buf_parts:
            buf_title = sec.title
            buf_parts = [piece]
            continue
        trial = "\n\n".join(buf_parts + [piece])
        if estimate_tokens(trial) <= max_tokens and (
            estimate_tokens("\n\n".join(buf_parts)) < min_tokens
            or estimate_tokens(piece) < min_tokens // 2
        ):
            buf_parts.append(piece)
        else:
            # if current buffer still small, keep merging unless oversize
            if estimate_tokens("\n\n".join(buf_parts)) < min_tokens and estimate_tokens(
                trial
            ) <= max_tokens:
                buf_parts.append(piece)
            else:
                flush()
                buf_title = sec.title
                buf_parts = [piece]
    flush()

    out: list[RawChunk] = []
    for title, body in merged:
        out.append(
            RawChunk(
                title=title,
                body=body,
                token_estimate=estimate_tokens(body),
                network=_detect_network(title, body),
                po_id=_detect_po(title, body),
            )
        )
    return out
