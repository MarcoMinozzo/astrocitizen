# Sprint — AC-191 Knowledge schema (KB-1 base)

**Data:** 2026-07-23  
**Estado:** concluido  
**Base:** [EPICO_E19_BASE_CONHECIMENTO_RAG.md](EPICO_E19_BASE_CONHECIMENTO_RAG.md) · AC-190

## Entregas

1. Modelos `KnowledgeDocument` / `KnowledgeChunk` (`knowledge/models.py`)
2. SQLite **schema v6**: `knowledge_documents`, `knowledge_chunks`
3. CRUD em `SqliteArchive` (upsert/get/list/soft-delete)
4. Campos citaveis: `source_id`, `trust_tier`, `chunk_hash` / `content_hash`

## Fora deste slice

- Ingest T3 docs/atlas (AC-192)
- FTS / `knowledge search` (AC-193)
- RetrieverPort / embeddings

## DoD

- [x] Tabelas dedicadas (nao misturadas com FITS)
- [x] Round-trip document + chunk
- [x] Soft-delete documento cascata em chunks
- [x] Testes + backlog AC-191
