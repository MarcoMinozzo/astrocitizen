# Sprint — AC-199 Gold questions + citation rate

**Data:** 2026-07-23  
**Estado:** concluido  
**Depende:** AC-193 / AC-196

## Entregas

1. `qa/gold-questions.v0.json` — 10 perguntas activas; target citation rate ≥0.8
2. `knowledge/eval_gold.py` — `evaluate_gold` (hit = expected_source_id citado)
3. CLI `knowledge eval-gold` (`--mode`, `--out`, `--json`)

## Metrica

`citation_rate = n_hits / n_questions`  
Hit se **qualquer** `expected_source_ids` aparecer nas citacoes top-k do `answer_help`.

## Fora deste slice

- Eval semantico LLM-as-judge
- AC-200 spectrum RAG + AC-107

## DoD

- [x] Gold set ≥10 perguntas
- [x] Target ≥80% e eval CLI mensuravel
- [x] Testes AC-199
