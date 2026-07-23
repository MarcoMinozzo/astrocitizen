---
chunk_id: docs-workflows-001
source_id: docs-workflows
path: docs/WORKFLOWS.md
title: Introduction
trust_tier: T3
lang: pt
topics: ["workflows", "ux"]
po_id: null
network: null
pipeline_stage: help
token_estimate: 273
chunk_hash: "sha256:bcac5d054f9fe4ef4c21aae490d419ce5aedbb907ff0683e585ac906570b1980"
corpus_version: 0.1.0-kb1
---

## Introduction

# Workflows e jornada do usuÿrio ÿ AstroCitizen

**Versÿo:** 1.0  
**Data:** 2026-07-21  
**Status:** especificaÿÿo de produto  
**Fontes:** [ESCOPO_GERAL_E_REGRAS_DE_NEGOCIO.md](ESCOPO_GERAL_E_REGRAS_DE_NEGOCIO.md) (RN-*), [ARQUITETURA.md](ARQUITETURA.md), [PRODUCT_BACKLOG.md](PRODUCT_BACKLOG.md) (AC-*), [PROGRAMAS_OBSERVACIONAIS.md](PROGRAMAS_OBSERVACIONAIS.md) (PO-*)

---

## 1. Propÿsito deste documento

Formaliza a **jornada do usuÿrio** na plataforma: modos de uso, passos, estados, alternativas e mapeamento para casos de uso e backlog.

O fluxo de **domÿnio** (entidades, RN-*) jÿ estÿ em `ESCOPO_GERAL_E_REGRAS_DE_NEGOCIO.md` ÿ5. Este documento traduz isso em **experiÿncia de produto** (CLI/GUI, decisÿes do observador, telas-alvo).

Contratos de serviÿo detalhados: ver `API_ALVO.md` (pendente).

---

## 2. Personas e perfis de uso

Na v1, **Observador** e **Gestor de programa** sÿo o mesmo usuÿrio (RN implÿcito em ÿ3 do escopo).

| Persona | Objetivo tÿpico | Modos mais usados |
|---------|-----------------|-------------------|
| **Observador iniciante** | Configurar site, ativar primeiro PO-*, planejar a noite | Configurar ? Planejar |
| **Observador de campo** | Executar sessÿo com hardware, registrar FITS | Executar ? Registrar |
| **Analista offline** | Importar dados, calibrar, produzir curva/espectro, exportar | Analisar ? Contribuir |
| **Gestor de campanhas** | Vÿrios PO-* ativos, prioridades, contribuiÿÿes pendentes | Configurar ? Planejar ? Contribuir |

Cada persona pode usar **apenas um subconjunto** da jornada (RN-055: planejamento sem hardware; anÿlise dias depois ÿ RN-073).

---
