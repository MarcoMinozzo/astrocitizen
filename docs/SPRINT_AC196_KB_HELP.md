# Sprint — AC-196 Ajuda grounded (CLI/GUI)

**Data:** 2026-07-23  
**Estado:** concluido  
**Depende:** AC-194 / AC-195

## Entregas

1. `knowledge/assistant.py` — `answer_help` extractivo (retrieval obrigatorio; sem LLM)
2. CLI `knowledge ask "<pergunta>"` — resposta + citacoes `chunk_id`/`source_id`/`trust_tier`
3. GUI HelpPanel — caixa "Perguntar KB" + archive injectado
4. Locales pt/es/en para labels da pergunta

## Fora deste slice

- Narrador LLM (AC-107) ancorado nas mesmas citacoes
- Glossario (AC-198)
- Gold QA citation rate (AC-199)

## DoD

- [x] Sem hits → recusa (nao inventa)
- [x] Com hits → resposta extractiva + lista de citacoes
- [x] CLI + GUI
- [x] Testes AC-196
