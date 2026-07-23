# Knowledge base (E19 / KB-0)

Scaffold interno para RAG futuro. **Nao** e indice de FITS nem dados do observador.

**Estado:** KB-0…KB-4 ✅ (FTS + RetrieverPort + embeddings RRF) · MCP AC-197 / Ajuda AC-196 pendentes.

## Layout

```text
knowledge-base/
  README.md                 # este ficheiro
  catalog.json              # fontes registadas (path + trust + license)
  taxonomy.json             # topics, networks, po_id, trust tiers
  manifest.json             # versao do corpus / ingest (KB-1: 51 chunks)
  conflict-policy.md        # T1..T5 e resolucao de conflitos
  licenses/                 # textos / notas de licenca
  templates/chunk.md        # frontmatter de chunk
  qa/gold-questions.v0.json # gold set (placeholder ate AC-199)
  processed/                # markdown processado (offline ingest)
  chunks/v1/                # chunks versionados (offline ingest)
```

## Fases

| Fase | Estado |
|------|--------|
| KB-0 scaffold | ✅ AC-190 |
| KB-1 conteudo T3 | ✅ AC-192 (51 chunks) |
| KB-2 FTS | ✅ AC-193 |
| KB-3 Retriever/MCP | ✅ RetrieverPort AC-194 · MCP AC-197 aberto |
| KB-4 embeddings | ✅ AC-195 (hashing-ngram + RRF) |
| KB-5 produto | aberto |

Ver [docs/EPICO_E19_BASE_CONHECIMENTO_RAG.md](../docs/EPICO_E19_BASE_CONHECIMENTO_RAG.md).

## Regras

- Sem PDF de livros no git.
- Sem credenciais / FITS / dados pessoais no corpus.
- Ingestao e offline; runtime so le chunks/indice.
- Cite sempre `source_id` / `chunk_id` / `trust_tier` nas respostas RAG.
