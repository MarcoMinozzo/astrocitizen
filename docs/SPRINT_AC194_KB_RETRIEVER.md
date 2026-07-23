# Sprint — AC-194 RetrieverPort (KB-3 partial)

**Data:** 2026-07-23  
**Estado:** concluido  
**Depende:** AC-193

## Entregas

1. `ports/retriever.py` — `RetrieverPort`, `Citation`, `RetrieveFilters`
2. `adapters/sqlite/fts_retriever.py` — `SqliteFtsRetriever`
3. Filtro `topic` (JSON) alem de PO-*, rede, lang, trust_tier, source_id
4. CLI:
   - `knowledge search` via RetrieverPort (+ `--topic`)
   - `knowledge get <chunk_id>`
   - `knowledge sources`

## Fora deste slice

- MCP `kb_search` / `kb_get_chunk` (AC-197)
- Embeddings / RRF (AC-195)
- Assistente Ajuda GUI (AC-196)
- Gold citation eval (AC-199)

## DoD

- [x] Porta hexagonal utilizavel sem LLM
- [x] Citacoes com `chunk_id` / `source_id` / `trust_tier`
- [x] Filtros PO-* / rede / topic / lang
- [x] Testes AC-194
