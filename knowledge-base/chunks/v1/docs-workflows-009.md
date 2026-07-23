---
chunk_id: docs-workflows-009
source_id: docs-workflows
path: docs/WORKFLOWS.md
title: Sequÿncia
trust_tier: T3
lang: pt
topics: ["workflows", "ux"]
po_id: PO-A01
network: aavso
pipeline_stage: help
token_estimate: 222
chunk_hash: "sha256:3c15d9d6bd7b54d52675ec5530301039f1d4e0280fe25e24f9d54fd92f459ae0"
corpus_version: 0.1.0-kb1
---

## Sequÿncia

```mermaid
sequenceDiagram
  participant U as Observador
  participant P as Planejamento
  participant O as Observatÿrio
  participant A as Anÿlise
  participant X as Contribuiÿÿo

  U->>P: Gerar ProgramaDiario (noite N)
  P->>P: Efemÿrides + meteo + viabilidade
  U->>P: Publicar plano
  U->>O: Iniciar Sessÿo (snapshot)
  loop Blocos fotometria
    O->>O: Expor alvo + comps
    O->>O: Registrar FITS ? BD
  end
  U->>O: Encerrar Sessÿo
  U->>A: Calibrar frames
  U->>A: Fotometria abertura + diferencial
  A->>A: Curva de luz ? BD (pontos)
  U->>X: Export AAVSO
  X->>X: Validar formato atlas
  U->>X: Exportar / enviar
```

## Passos numerados (critÿrio de aceite de produto)

| # | Fase | Entregÿvel |
|---|------|------------|
| 1 | Configurar | Site + PO-A01 ativo |
| 2 | Planejar | ProgramaDiario com bloco(s) variÿvel viÿvel |
| 3 | Executar | ?1 Observacao FITS com metadados completos |
| 4 | Analisar | ProdutoAnalise curva de luz (pontos no BD) |
| 5 | Contribuir | ContribuicaoRede AAVSO `validado` ou `exportado` |

**Itens backlog associados:** AC-081, AC-091, AC-092, AC-093.

---
