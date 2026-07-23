---
chunk_id: docs-analise-espectral-003
source_id: docs-analise-espectral
path: docs/ANALISE_ESPECTRAL_ASSISTIDA.md
title: 5. LLM (planejado) — nao substitui medidas
trust_tier: T3
lang: pt
topics: ["spectrum", "analysis"]
po_id: PO-B03
network: bess
pipeline_stage: help
token_estimate: 177
chunk_hash: "sha256:56c55c0934c2da68ec1d2f50f5e0fb52afcf3c17e433749c404a39b4203e45c1"
corpus_version: 0.1.0-kb1
---

## 5. LLM (planejado) — nao substitui medidas

Principio: **medidas fisicas primeiro; linguagem depois**.

| ID | Ideia |
|----|-------|
| AC-107 | Narrativa LLM a partir do `spectrum_report` (e so dele + contexto citado) |
| AC-108 | Modo offline / opt-in; sem LLM o fluxo AC-106 continua a funcionar |
| AC-109 | Guardrails: nao inventar linhas; citar FEATURES do relatorio; marcar incerteza |

A camada LLM **nao** deve recalcular fluxos nem classificar SN sozinha. Idealmente usa **RAG (E19)** para citar docs ARAS/BeSS/atlas internos.

---

## 6. Relacao com RAG (E19)

A base de conhecimento interna (E19) alimenta respostas contextualizadas, por exemplo:

- “o que significa O2 A no meu relatorio?” → chunk atlas / guia espectral;
- “proximo passo PO-B03 / ARAS” → docs de workflow e redes.

Ver [EPICO_E19_BASE_CONHECIMENTO_RAG.md](EPICO_E19_BASE_CONHECIMENTO_RAG.md).
