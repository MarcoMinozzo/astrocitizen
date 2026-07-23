# Sprint — AC-200 Spectrum RAG + AC-107 offline

**Data:** 2026-07-23  
**Estado:** concluido  
**Depende:** AC-106, AC-194

## Entregas

1. `knowledge/spectrum_explain.py` — cues do `spectrum_report` + RAG KB
2. Narrativa extractiva (AC-107 offline; sem LLM) com guardrail de medidas
3. CLI `analyze spectrum-explain --report <txt>`

## Contrato

- **Medidas / FEATURES:** so do ficheiro AC-106
- **Contexto:** passagens KB (topic spectrum / BeSS docs)
- LLM pluggable fica para AC-108; este slice funciona offline

## Fora deste slice

- Provider LLM real (AC-108)
- Guardrails LLM-as-judge (AC-109)

## DoD

- [x] Explicar relatorio sem alterar AC-106
- [x] Citacoes KB obrigatorias quando corpus responde
- [x] Testes AC-200
