"""Explicar spectrum_report com RAG (AC-200) + narrativa extractiva (AC-107 offline).

Nao usa LLM neste slice: combina FEATURES do relatorio AC-106 com passagens KB
(BeSS/ARAS/docs). AC-106 permanece a fonte de medidas.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from astrocitizen.knowledge.assistant import HelpAnswer
from astrocitizen.ports.retriever import Citation, RetrieveFilters

_FEATURE_LINE_RE = re.compile(
    r"(?P<name>H-alpha|H-beta|H-gamma|H-delta|He I \d+|Na D|Si II \d+|O2 A|Ca II \d+)",
    re.IGNORECASE,
)
_CLASS_HINT_RE = re.compile(r"class[_\s-]?hint[:\s]+([^\n]+)", re.IGNORECASE)
_TOP_LINE_RE = re.compile(r"top[_\s-]?line[:\s]+([^\n]+)", re.IGNORECASE)


@dataclass
class SpectrumExplainResult:
    report_path: str | None
    narrative: str
    features_used: list[str] = field(default_factory=list)
    citations: list[Citation] = field(default_factory=list)
    grounded: bool = False
    mode: str = "hybrid"

    def format_text(self) -> str:
        lines = [self.narrative.strip(), ""]
        if self.citations:
            lines.append("Citacoes KB (corpus, nao medidas):")
            for i, c in enumerate(self.citations, start=1):
                lines.append(f"  [{i}] {c.citation_label()}")
                if c.snippet:
                    lines.append(f"      {c.snippet.replace(chr(10), ' ')[:200]}")
        lines.append("")
        lines.append(
            "Guardrail: medidas e FEATURES vêm so do spectrum_report (AC-106). "
            "Passagens KB nao alteram linhas/SNR."
        )
        return "\n".join(lines).rstrip() + "\n"


def extract_report_cues(report_text: str) -> dict[str, Any]:
    text = report_text or ""
    features = []
    for m in _FEATURE_LINE_RE.finditer(text):
        name = m.group("name")
        if name not in features:
            features.append(name)
    class_hint = None
    m = _CLASS_HINT_RE.search(text)
    if m:
        class_hint = m.group(1).strip()
    top_line = None
    m = _TOP_LINE_RE.search(text)
    if m:
        top_line = m.group(1).strip()
    return {
        "features": features,
        "class_hint": class_hint,
        "top_line": top_line,
        "excerpt": text[:1200],
    }


def build_spectrum_query(cues: dict[str, Any]) -> str:
    parts = ["spectrum_report", "BeSS", "ARAS", "espectroscopia"]
    if cues.get("class_hint"):
        parts.append(str(cues["class_hint"]))
    if cues.get("top_line"):
        parts.append(str(cues["top_line"]))
    parts.extend(cues.get("features") or [])
    return " ".join(parts)


def explain_spectrum_report(
    retriever: Any,
    report_text: str,
    *,
    report_path: str | None = None,
    limit: int = 5,
    mode: str = "hybrid",
) -> SpectrumExplainResult:
    """Narrativa extractiva ancorada no relatorio + KB (sem inventar linhas)."""
    text = (report_text or "").strip()
    if not text:
        return SpectrumExplainResult(
            report_path=report_path,
            narrative=(
                "Relatorio spectrum_report vazio. Gere primeiro com "
                "`analyze spectrum-report` (AC-106)."
            ),
            grounded=False,
            mode=mode,
        )

    cues = extract_report_cues(text)
    query = build_spectrum_query(cues)
    filters = RetrieveFilters(topic="spectrum")
    hits = retriever.search(query, limit=limit, filters=filters, mode=mode)
    if not hits:
        # fallback sem filtro topic
        hits = retriever.search(query, limit=limit, mode=mode)

    parts: list[str] = [
        "Explicacao grounded (AC-200 / AC-107 offline — sem LLM):",
        "",
        "1) Medidas do spectrum_report (AC-106 — fonte de verdade):",
    ]
    if cues["features"]:
        parts.append("   FEATURES: " + ", ".join(cues["features"]))
    else:
        parts.append("   (nenhuma linha do catalogo detectada no texto do relatorio)")
    if cues.get("class_hint"):
        parts.append(f"   class_hint: {cues['class_hint']}")
    if cues.get("top_line"):
        parts.append(f"   top_line: {cues['top_line']}")
    parts.append("")
    parts.append("2) Contexto do corpus (BeSS/ARAS/docs — citavel, nao medida):")
    if not hits:
        parts.append(
            "   Sem passagens KB. Corra `knowledge ingest` / `embed` e tente de novo."
        )
        grounded = False
    else:
        grounded = True
        for i, h in enumerate(hits, start=1):
            title = (h.title or h.source_id).strip()
            snip = (h.snippet or "").replace("\n", " ").strip()[:240]
            parts.append(f"   {i}. {title} → {h.citation_label()}")
            if snip:
                parts.append(f"      {snip}")
    parts.append("")
    parts.append(
        "3) Sintese: use as FEATURES acima para discutir a observacao; "
        "use as citacoes KB so para procedimento/rede (ex. BeSS). "
        "Nao invente linhas ausentes do relatorio."
    )
    return SpectrumExplainResult(
        report_path=report_path,
        narrative="\n".join(parts),
        features_used=list(cues["features"]),
        citations=list(hits or []),
        grounded=grounded,
        mode=mode,
    )


def explain_spectrum_report_file(
    retriever: Any,
    path: Path,
    *,
    limit: int = 5,
    mode: str = "hybrid",
) -> SpectrumExplainResult:
    p = Path(path)
    text = p.read_text(encoding="utf-8", errors="replace") if p.is_file() else ""
    return explain_spectrum_report(
        retriever, text, report_path=str(p), limit=limit, mode=mode
    )


def to_help_answer(result: SpectrumExplainResult) -> HelpAnswer:
    """Adapter para o mesmo formato de Ajuda grounded."""
    return HelpAnswer(
        question="explain spectrum_report",
        answer=result.narrative,
        citations=list(result.citations),
        grounded=result.grounded,
        mode=result.mode,
        refusal_reason=None if result.grounded else "no_kb_or_empty_report",
    )
