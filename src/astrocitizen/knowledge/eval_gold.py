"""Eval gold questions — citation rate (AC-199)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from astrocitizen.knowledge.assistant import answer_help
from astrocitizen.knowledge.scaffold import default_kb_root, load_json


@dataclass
class GoldQuestionResult:
    question_id: str
    question: str
    grounded: bool
    cited_source_ids: list[str]
    expected_source_ids: list[str]
    hit: bool
    chunk_ids: list[str] = field(default_factory=list)


@dataclass
class GoldEvalReport:
    set_id: str
    n_questions: int
    n_hits: int
    citation_rate: float
    target: float
    passed: bool
    results: list[GoldQuestionResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "set_id": self.set_id,
            "n_questions": self.n_questions,
            "n_hits": self.n_hits,
            "citation_rate": round(self.citation_rate, 4),
            "target": self.target,
            "passed": self.passed,
            "results": [
                {
                    "id": r.question_id,
                    "hit": r.hit,
                    "grounded": r.grounded,
                    "cited_source_ids": r.cited_source_ids,
                    "expected_source_ids": r.expected_source_ids,
                    "chunk_ids": r.chunk_ids,
                }
                for r in self.results
            ],
        }


def gold_questions_path(kb_root: Path | None = None) -> Path:
    return (kb_root or default_kb_root()) / "qa" / "gold-questions.v0.json"


def load_gold_questions(kb_root: Path | None = None) -> dict[str, Any]:
    path = gold_questions_path(kb_root)
    if not path.is_file():
        return {"set_id": "missing", "citation_rate_target": 0.8, "questions": []}
    return load_json(path)


def evaluate_gold(
    retriever: Any,
    *,
    kb_root: Path | None = None,
    limit: int = 5,
    mode: str = "hybrid",
) -> GoldEvalReport:
    """Corre answer_help por pergunta; hit se algum expected_source_id for citado."""
    data = load_gold_questions(kb_root)
    target = float(data.get("citation_rate_target") or 0.8)
    questions = list(data.get("questions") or [])
    results: list[GoldQuestionResult] = []
    hits = 0
    for q in questions:
        if not isinstance(q, dict):
            continue
        qid = str(q.get("id") or "")
        text = str(q.get("question") or "").strip()
        expected = [str(s) for s in (q.get("expected_source_ids") or [])]
        ans = answer_help(retriever, text, limit=limit, mode=mode)  # type: ignore[arg-type]
        cited = []
        chunk_ids = []
        for c in ans.citations:
            if c.source_id and c.source_id not in cited:
                cited.append(c.source_id)
            chunk_ids.append(c.chunk_id)
        hit = bool(expected) and any(s in cited for s in expected)
        if hit:
            hits += 1
        results.append(
            GoldQuestionResult(
                question_id=qid,
                question=text,
                grounded=ans.grounded,
                cited_source_ids=cited,
                expected_source_ids=expected,
                hit=hit,
                chunk_ids=chunk_ids,
            )
        )
    n = len(results)
    rate = (hits / n) if n else 0.0
    return GoldEvalReport(
        set_id=str(data.get("set_id") or "gold"),
        n_questions=n,
        n_hits=hits,
        citation_rate=rate,
        target=target,
        passed=rate >= target and n > 0,
        results=results,
    )


def write_eval_report(report: GoldEvalReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
