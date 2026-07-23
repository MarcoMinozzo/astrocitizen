---
chunk_id: docs-workflows-004
source_id: docs-workflows
path: docs/WORKFLOWS.md
title: 5.3 Ativar programas observacionais (PO-*)
trust_tier: T3
lang: pt
topics: ["workflows", "ux"]
po_id: null
network: null
pipeline_stage: help
token_estimate: 209
chunk_hash: "sha256:78110316e3bf15cf0f91ebaae746f87b02abadd474e406bd47822f211223de39"
corpus_version: 0.1.0-kb1
---

## 5.3 Ativar programas observacionais (PO-*)

**Objetivo:** campanhas de longo prazo alimentam candidatos do programa diÿrio (RN-040ÿ047).

```mermaid
stateDiagram-v2
  [*] --> rascunho: Instanciar template PO-*
  rascunho --> ativo: Revisar alvos/cadÿncia/rede
  ativo --> pausado: Pausar campanha
  pausado --> ativo: Retomar
  ativo --> arquivado: Encerrar
  pausado --> arquivado: Encerrar
```

| Passo | Aÿÿo | Sistema | Saÿda |
|-------|------|---------|-------|
| 1 | Escolher template **PO-*** no catÿlogo | Carrega metadados (tÿcnica, rede, produto mÿnimo) | ProgramaObservacional `rascunho` |
| 2 | Configurar alvos, cadÿncia, prioridade, config. instrumental padrÿo | Valida contra CS-* / PO-* | Programa editÿvel |
| 3 | Ativar | Sÿ `ativo` entra no gerador diÿrio (RN-041) | Programa `ativo` |
| 4 | (Opcional) Ativar segundo programa | Conflitos resolvidos por prioridade depois (RN-042) | Multi-programa |

**Painel de gestÿo** (requisito ÿ8 escopo): lista programas, prÿxima janela, obs. recentes, export pendente, alertas (AC-074).

**Backlog:** AC-022, AC-023, AC-081ÿ088.

---

## 6. Modo 2 ÿ Planejar
