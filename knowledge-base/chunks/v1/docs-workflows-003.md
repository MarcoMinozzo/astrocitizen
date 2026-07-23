---
chunk_id: docs-workflows-003
source_id: docs-workflows
path: docs/WORKFLOWS.md
title: 5.1 Cadastrar e selecionar Site
trust_tier: T3
lang: pt
topics: ["workflows", "ux"]
po_id: null
network: null
pipeline_stage: help
token_estimate: 282
chunk_hash: "sha256:18ce96db02daf9ababcb8ad8fb100d28e303a9564006fc4c80a6555307740a34"
corpus_version: 0.1.0-kb1
---

## 5.1 Cadastrar e selecionar Site

**Objetivo:** todo planejamento e registro referem-se a um local explÿcito (RN-001).

| Passo | Aÿÿo do usuÿrio | Sistema | Saÿda |
|-------|-----------------|---------|-------|
| 1 | Criar Site (nome, lat, lon, alt, fuso) | Valida coordenadas | Site no BD |
| 2 | Opcional: limiares (alt. mÿn., meteo, crepÿsculo) | Defaults da plataforma + override | SiteProfile completo |
| 3 | Definir Site **ativo** | Recalcula caches de efemÿrides/meteo se houver plano | Contexto global da sessÿo UI/CLI |

**Alternativas:** editar Site existente; trocar Site ativo ? ProgramaDiario em ediÿÿo deve ser recalculado (RN-002).

**Backlog:** AC-020, AC-072.

---

## 5.2 Inventÿrio de equipamento

**Objetivo:** blocos do programa diÿrio declaram configuraÿÿo instrumental vÿlida (RN-030ÿ035).

| Passo | Aÿÿo | Sistema | Saÿda |
|-------|------|---------|-------|
| 1 | Registrar item (montagem, cÿmera, focuser, filtro, espectrÿgrafoÿ) | Tipo + metadados + backend | Equipamento no BD |
| 2 | Marcar disponibilidade (manutenÿÿo) | RN-035 | Flag no inventÿrio |
| 3 | Criar **ConfiguraÿÿoInstrumental** (preset) | Valida compatibilidade tÿcnica | Preset reutilizÿvel |
| 4 | Escolher backend de cÿmera: `sim` \| `alpaca` \| `udrv` | AC-046 | Preferÿncia persistida |

**Alternativas:** diagnÿstico de conexÿo Alpaca/udrv (sem Sessao ativa ÿ RN-090).

**Backlog:** AC-021, AC-040ÿ047, AC-072.

---
