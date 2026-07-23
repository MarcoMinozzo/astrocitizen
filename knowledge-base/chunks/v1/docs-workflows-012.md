---
chunk_id: docs-workflows-012
source_id: docs-workflows
path: docs/WORKFLOWS.md
title: 17. Mapeamento SaaS + Desktop (D-008)
trust_tier: T3
lang: pt
topics: ["workflows", "ux"]
po_id: PO-A01
network: aavso
pipeline_stage: help
token_estimate: 312
chunk_hash: "sha256:44fd6f724052227fe105fb580b4d3f6c0b22a9412c54f8fd047d70ed96ff6281"
corpus_version: 0.1.0-kb1
---

## 17. Mapeamento SaaS + Desktop (D-008)

A jornada dos quatro modos distribui-se entre os dois m?dulos de produto. Detalhe: [ARQUITETURA_SAAS_DESKTOP.md](ARQUITETURA_SAAS_DESKTOP.md).

| Modo | SaaS (web) | Desktop (observat?rio) |
|------|------------|------------------------|
| **1. Configurar** | Sites, programas PO-*, invent?rio (cadastro) | Estado de conex?o do equipamento; espelho local |
| **2. Planejar** | Gerar, editar e publicar ProgramaDiario | Pull do plano publicado; checklist pr?-noite |
| **3. Executar** | Monitoramento (futuro) | Sess?o, hardware, aquisi??o, registro FITS |
| **4. Analisar e contribuir** | Redu??o, produtos, export AAVSO/MPC/ | Opcional: preview local; sync de observa??es |

## Fluxo t?pico ponta a ponta

1. Usu?rio configura site e PO-A01 no **SaaS**.
2. Planeja e publica ProgramaDiario no **SaaS**.
3. **Desktop** sincroniza plano (pull).
4. Observador executa sess?o no **Desktop** (offline permitido).
5. **Desktop** envia observa??es e FITS (push + upload).
6. Usu?rio analisa e exporta no **SaaS**.

## UI por m?dulo

| ?rea WORKFLOWS §4 | SaaS | Desktop |
|-------------------|:----:|:-------:|
| In?cio | Dashboard workspace | Console de sess?o + status sync |
| Sites / Equipamento / Programas | Principal | Cache + diagn?stico hardware |
| Planejamento | Principal | Leitura do plano sincronizado |
| Observat?rio |  | Principal |
| Arquivo / An?lise / Contribui??o | Principal | Consulta cache + fila pendente |

Modo **SaaS-only** (sem Desktop): importar FITS via web e seguir an?lise/contribui??o (ver MODELO_DE_SINCRONIZACAO §12).
