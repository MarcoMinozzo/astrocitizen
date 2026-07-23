"""Assistente Ajuda grounded — so com citacoes (AC-196). LLM opcional/futuro."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from astrocitizen.ports.retriever import Citation, RetrieveFilters

SearchMode = Literal["fts", "vector", "hybrid"]


@dataclass
class HelpAnswer:
    """Resposta extractiva ancorada em passagens; nunca inventa sem hits."""

    question: str
    answer: str
    citations: list[Citation] = field(default_factory=list)
    grounded: bool = False
    mode: str = "hybrid"
    refusal_reason: str | None = None

    def format_text(self) -> str:
        lines = [self.answer.strip(), ""]
        if self.citations:
            lines.append("Citacoes:")
            for i, c in enumerate(self.citations, start=1):
                title = (c.title or "").strip()
                label = c.citation_label()
                snip = (c.snippet or "").replace("\n", " ").strip()
                lines.append(f"  [{i}] {label}" + (f" — {title}" if title else ""))
                if snip:
                    lines.append(f"      {snip[:200]}")
        return "\n".join(lines).rstrip() + "\n"


def answer_help(
    retriever: Any,
    question: str,
    *,
    limit: int = 5,
    mode: SearchMode = "hybrid",
    filters: RetrieveFilters | None = None,
) -> HelpAnswer:
    """Retrieval obrigatorio; resposta = sintese extractiva das passagens.

    Sem hits → recusa explicita (nao alucina). Sem LLM neste slice.
    """
    q = (question or "").strip()
    if not q:
        return HelpAnswer(
            question=q,
            answer="Pergunta vazia. Escreva uma questao sobre o produto ou redes.",
            grounded=False,
            mode=mode,
            refusal_reason="empty_question",
        )

    hits = retriever.search(q, limit=limit, filters=filters, mode=mode)
    if not hits:
        return HelpAnswer(
            question=q,
            answer=(
                "Nao encontrei passagens na base de conhecimento para esta pergunta. "
                "Reformule, ou confirme que o corpus foi ingerido "
                "(`astrocitizen knowledge ingest` / `embed`)."
            ),
            citations=[],
            grounded=False,
            mode=mode,
            refusal_reason="no_hits",
        )

    # Resposta extractiva: titulo + snippet das top passagens (sem inventar)
    parts: list[str] = [
        "Com base apenas nas passagens recuperadas (sem LLM):",
        "",
    ]
    for i, h in enumerate(hits, start=1):
        title = (h.title or h.source_id or h.chunk_id).strip()
        snip = (h.snippet or "").replace("\n", " ").strip()
        if not snip and h.body:
            snip = h.body.replace("\n", " ").strip()[:220]
        parts.append(f"{i}. {title}")
        if snip:
            parts.append(f"   {snip[:280]}")
        parts.append(f"   → {h.citation_label()}")
        parts.append("")
    parts.append(
        "Nota: esta resposta e extractiva. Nao substitui medidas cientificas "
        "(fotometria, spectrum-report, plate-solve)."
    )
    return HelpAnswer(
        question=q,
        answer="\n".join(parts).rstrip(),
        citations=list(hits),
        grounded=True,
        mode=mode,
    )
