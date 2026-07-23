---
chunk_id: docs-workflows-005
source_id: docs-workflows
path: docs/WORKFLOWS.md
title: 6.1 Gerar Programa Diÿrio
trust_tier: T3
lang: pt
topics: ["workflows", "ux"]
po_id: PO-J03
network: null
pipeline_stage: help
token_estimate: 412
chunk_hash: "sha256:84c389ad71ef2271f08b4c09b822a9e63946fff4c2231a331a5b5f71550a10d9"
corpus_version: 0.1.0-kb1
---

## 6.1 Gerar Programa Diÿrio

**Objetivo:** um plano por Site e por noite (RN-050), combinando ciÿncia, cÿu, meteo e equipamento.

| Passo | Aÿÿo | Sistema | Saÿda |
|-------|------|---------|-------|
| 1 | Selecionar data (noite civil do Site, RN-004) | ÿ | Data alvo |
| 2 | **Gerar / atualizar** plano | Programas ativos + EphemerisPort + MeteoPort + inventÿrio | ProgramaDiario `rascunho` |
| 3 | Revisar lista de **BlocosObservacionais** | Cada bloco: alvo, janela UT, Alt/Az, airmass, programa origem | Lista ordenada |
| 4 | Inspecionar status por bloco | RN-053 | `candidato`, `agendado`, `inviavel_*`, ÿ |
| 5 | Editar manualmente (reordenar, incluir alvo, remover) | RN-052; motivo preservado para inviÿveis | Plano ajustado |
| 6 | **Publicar** plano | Estado `publicado` | Plano pronto para sessÿo ou referÿncia |

**Informaÿÿo mÿnima por bloco** (escopo ÿ8): alvo, janela UT, altitude, airmass, status cÿu/meteo/equip, config. instrumental, programa, prioridade, notas.

```mermaid
flowchart TD
  A[Programas ativos] --> G[Gerador ProgramaDiario]
  B[Efemÿrides Astropy/Astroquery] --> G
  C[Meteo do Site] --> G
  D[Equipamento disponÿvel] --> G
  G --> E{Por bloco}
  E --> F1[Viÿvel: agendado]
  E --> F2[Inviÿvel cÿu]
  E --> F3[Inviÿvel meteo]
  E --> F4[Inviÿvel equip]
  F2 --> H[Visÿvel com motivo RN-054]
  F3 --> H
  F4 --> H
```

**Alternativas:**

- **Meteo indisponÿvel:** blocos marcados; usuÿrio pode sobrescrever com `meteo_manual=true` na sessÿo (RN-023).
- **Efemÿride remota falhou:** cache local ou `efemÿride indisponÿvel` (RN-014).
- **Modo planejamento puro:** sem hardware conectado (RN-055).

**Backlog:** AC-030ÿ037, AC-073.

---

## 6.2 Checklist prÿ-noite (operacional)

Checklist sugerido na UI antes de `em_execucao` (nÿo bloqueante, configurÿvel):

1. Site e data corretos  
2. Previsÿo meteo revisada  
3. Configuraÿÿo instrumental dos blocos agendados conferida  
4. Masters de calibraÿÿo recentes (PO-J03) ÿ alerta se ausentes  
5. Espaÿo em disco / caminho de artefatos  
6. Backends de hardware testados (ou simulador selecionado)

---

## 7. Modo 3 ÿ Executar
