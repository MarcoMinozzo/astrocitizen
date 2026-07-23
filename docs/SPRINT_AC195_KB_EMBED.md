# Sprint — AC-195 Embeddings locais + RRF (KB-4)

**Data:** 2026-07-23  
**Estado:** concluido  
**Depende:** AC-193 / AC-194

## Entregas

1. Schema SQLite **v8** — `knowledge_chunk_embeddings` (BLOB float32)
2. `HashingNgramEmbedder` (stdlib; D-010 — sem torch no core)
3. `rebuild_embeddings` + manifest `index.embeddings` (fase KB-4)
4. `HybridRetriever` — modos `fts` | `vector` | `hybrid` (RRF)
5. CLI:
   - `knowledge embed`
   - `knowledge search --mode hybrid|fts|vector`

## Fora deste slice

- `multilingual-e5-small` / sentence-transformers (extra opcional futuro)
- MCP (AC-197) — ver [SPRINT_AC197_KB_MCP.md](SPRINT_AC197_KB_MCP.md)
- Gold citation eval (AC-199)

## DoD

- [x] Embeddings on-device sem dependencia pesada
- [x] Indice hibrido RRF lexical/vector
- [x] Fallback FTS se embeddings vazios
- [x] Testes AC-195
