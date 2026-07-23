---
chunk_id: docs-rn-001
source_id: docs-rn
path: docs/ESCOPO_GERAL_E_REGRAS_DE_NEGOCIO.md
title: Introduction
trust_tier: T3
lang: pt
topics: ["rules", "product"]
po_id: null
network: null
pipeline_stage: help
token_estimate: 252
chunk_hash: "sha256:a245f32dae1c87f9b4e7457a40d8e06bfef48294c093b9e311fb5d1d2f8190f9"
corpus_version: 0.1.0-kb1
---

## Introduction

# Escopo geral e regras de negócio

**Produto:** Plataforma de Astronomia Observacional Cidadã  
**Status:** Fase 0 — especificação de negócio (sem implementação)  
**Data:** 2026-07-20  
**Documentos relacionados:**  
`PLATAFORMA_OBSERVACIONAL.md` · `ESCOPO_CITIZEN_SCIENCE.md` · `STACK_TECNOLOGICA.md` · `REVISAO_ASTRONOMIA_OBSERVACIONAL.md`

---

## 1. Propósito do produto

A plataforma existe para **obter, planejar, executar, registrar e analisar observações astronômicas** no contexto de citizen science e pequenos observatórios.

Ela concentra cinco eixos de negócio inseparáveis:

1. **Dados astronômicos e efemérides observacionais** — o que está no céu, quando e onde observar.  
2. **Meteorologia do local de observação** — se as condições permitem observar.  
3. **Programa observacional diário** — o plano concreto da noite/dia.  
4. **Planejamento de observações e de equipamento** — alvos + instrumentos adequados.  
5. **Registro, análise e gestão dos programas observacionais** — do dado bruto ao produto científico e à campanha contínua.
6. **Persistência em bancos de dados** — todo resultado observacional alimenta BD(s) consultáveis (ver `PERSISTENCIA_E_BANCOS.md`).

O catálogo oficial de programas está em `PROGRAMAS_OBSERVACIONAIS.md` (PO-*, classes A–K). `ESCOPO_CITIZEN_SCIENCE.md` detalha capacidades científicas transversais. Este documento define **como o negócio opera** (programa diário, meteo, equipamento, registro, gestão).

---

## 2. Escopo geral (capacidade de negócio)
