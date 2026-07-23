---
chunk_id: docs-workflows-008
source_id: docs-workflows
path: docs/WORKFLOWS.md
title: 9. Modo 4 (cont.) ÿ Contribuir ÿs redes
trust_tier: T3
lang: pt
topics: ["workflows", "ux"]
po_id: PO-A01
network: aavso
pipeline_stage: help
token_estimate: 236
chunk_hash: "sha256:39008e7af12ab905ad557471a993f883b06001e55812018be1d89e78f3dab56b"
corpus_version: 0.1.0-kb1
---

## 9. Modo 4 (cont.) ÿ Contribuir ÿs redes

**Objetivo:** ContribuicaoRede atende produto mÿnimo do PO-* e formato do atlas (RN-080ÿ083).

| Passo | Aÿÿo | Sistema | Saÿda |
|-------|------|---------|-------|
| 1 | Abrir **Contribuiÿÿo** filtrada por programa/rede | Lista produtos elegÿveis | ÿ |
| 2 | Gerar pacote de export | Valida produto mÿnimo (RN-043, RN-080) | ContribuicaoRede `rascunho` |
| 3 | Revisar campos (atlas ATLAS_REPORTE) | Prÿ-preenchimento do BD | Rascunho editÿvel |
| 4 | Validar | Checks de formato | `validado` |
| 5 | Exportar arquivo / enviar | Credenciais locais (RN-082) | `exportado` / `enviado` |

Estados: `rascunho` ? `validado` ? `exportado` ? `enviado` | `rejeitado` (RN-081).

**Backlog:** E14, AC-093, AC-104, AC-112, etc.

---

## 10. Fluxo ponta a ponta de referÿncia ÿ PO-A01 (AAVSO)

Template: **Estrelas variÿveis (geral)** ÿ fotometria diferencial, rede AAVSO (P1).

## Prÿ-requisitos

- Site ativo configurado  
- Cÿmera + (opcional) montagem no inventÿrio  
- Programa instanciado de PO-A01, estado `ativo`, alvo variÿvel + comparaÿÿo + check definidos  
- Masters bias/dark/flat recentes (PO-J03 recomendado)
