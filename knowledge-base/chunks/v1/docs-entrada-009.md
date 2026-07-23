---
chunk_id: docs-entrada-009
source_id: docs-entrada
path: docs/ENTRADA_OBSERVACOES_POR_PO.md
title: 7. Prioridade de implementação dos canais
trust_tier: T3
lang: pt
topics: ["entrada", "channels"]
po_id: null
network: iota
pipeline_stage: help
token_estimate: 201
chunk_hash: "sha256:d0f8b9d599e6855b116928794dd0692ded63dcb57eb1ac1cb165e407ee5c10b4"
corpus_version: 0.1.0-kb1
---

## 7. Prioridade de implementação dos canais

| Ordem | Canal / superfície | Desbloqueia |
|-------|--------------------|-------------|
| 1 | **Import FITS** (GUI + CLI) | ✅ `import fits` + painel Import |
| 2 | **CRUD Site/Programa/Alvo na GUI** | ✅ metadados comuns |
| 3 | **Wizard Sessão** | ✅ IN-CAP usável no desktop |
| 3b | **CRUD Equipamento + Setup** | ✅ fecha AC-072 / liga programa |
| 4 | **Editor visual log + solar form** | ✅ Observar GUI + `observe log-visual` |
| 5 | **Timing/IOTA import previsão + vídeo** | ✅ pred+timing+video/LC · `SPRINT_IOTA_TIMING_ENTRADA5` |
| 6 | **Rádio CSV/HDF5** | ✅ `import radio` + GUI Radio · `SPRINT_RADIO_ENTRADA6` |
| 7 | Restantes especializações (speckle, polar, echelle) | ✅ `import echelle|speckle|polar` · `SPRINT_ESPECIALIDADES_ENTRADA7` |

**Epic ENTRADA (§7):** ✅ **fechado** (canais prioritários 1–7). Reduções científicas profundas e I02–I04 ficam em AC-* seguintes.

---
