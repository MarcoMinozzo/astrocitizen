# Sprint — AC-192 Knowledge ingest T3 (KB-1)

**Data:** 2026-07-23  
**Estado:** concluido  
**Depende:** AC-191

## Entregas

1. `knowledge/chunking.py` — split markdown ~200–700 tokens
2. `knowledge/frontmatter.py` + `knowledge/ingest.py` (UTF-8; fallback latin-1 se bytes invalidos, ex. WORKFLOWS.md)
3. CLI `knowledge ingest` / `knowledge validate`
4. Escrita `knowledge-base/processed/` + `chunks/v1/` (51 chunks T3)
5. Upsert SQLite + update `catalog.json` / `manifest.json` (fase KB-1)

## Fora deste slice

- FTS / `knowledge search` (AC-193)
- Embeddings / RetrieverPort
- Ingest T5 literatura

## DoD

- [x] Pipeline offline T3 docs + atlas
- [x] ≥50 chunks no corpus real (apos `knowledge ingest`)
- [x] Manifest `completed` + catalog `ingested`
- [x] Testes
