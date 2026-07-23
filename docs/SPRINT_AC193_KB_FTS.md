# Sprint — AC-193 Knowledge FTS5 + search (KB-2)

**Data:** 2026-07-23  
**Estado:** concluido  
**Depende:** AC-192

## Entregas

1. Schema SQLite **v7** — `knowledge_chunks_fts` (FTS5, unicode61 + remove_diacritics)
2. `SqliteArchive.rebuild_knowledge_fts` / `search_knowledge_chunks`
3. `knowledge/search.py` — `build_fts_query`, `rebuild_fts_index`, `search_knowledge`
4. CLI:
   - `astrocitizen knowledge index` — rebuild FTS + `manifest.index.fts`
   - `astrocitizen knowledge search "<query>"` — hits com `chunk_id` / `source_id` / `trust_tier` / snippet
5. Rebuild FTS automatico apos `knowledge ingest` (quando escreve BD)

## Fora deste slice

- `RetrieverPort` hexagonal (AC-194) — ver [SPRINT_AC194_KB_RETRIEVER.md](SPRINT_AC194_KB_RETRIEVER.md)
- Embeddings / RRF (AC-195)
- Eval citation rate gold-questions (AC-199)
- MCP `kb_search` (AC-197)

## DoD

- [x] FTS5 indexavel offline no Desktop
- [x] CLI `knowledge search` devolve citacoes (`chunk_id`, `source_id`, `trust_tier`)
- [x] Manifest `index.fts` preenchido; fase KB-2
- [x] Testes AC-193
