---
chunk_id: atlas-reporte-001
source_id: atlas-reporte
path: docs/atlas/ATLAS_REPORTE_OBSERVACOES.md
title: Introduction
trust_tier: T3
lang: pt
topics: ["networks", "export"]
po_id: null
network: null
pipeline_stage: help
token_estimate: 268
chunk_hash: "sha256:5bfdee93655ac3da5991a20cef4229740f933a634f46ae78d02085d1c2b80875"
corpus_version: 0.1.0-kb1
---

## Introduction

# Atlas interno — Registro e reporte de programas observacionais

**Produto:** AstroCitizen  
**Versão:** 1.0  
**Data:** 2026-07-21  
**Objetivo:** documentar, a partir de **fontes oficiais**, como cada programa/rede recebe observações: formulários, formatos, dados obrigatórios e canais de envio.  
**Catálogo de programas:** [`../PROGRAMAS_OBSERVACIONAIS.md`](../PROGRAMAS_OBSERVACIONAIS.md)

> Este atlas é a referência para exporters (`NetworkExportPort`) e para a validação do **produto mínimo** (RN-043 / RN-080).  
> Formatos externos mudam; sempre conferir o link oficial antes de implementar um exporter.

---

## 1. Como usar

| Coluna / seção | Significado |
|----------------|-------------|
| **Rede** | Organização que recebe o dado |
| **PO-*** | Programas AstroCitizen que alimentam essa rede |
| **Canal** | Web form, upload de arquivo, API, e-mail, hub regional |
| **Formato** | Especificação oficial do pacote de dados |
| **Dados-chave** | Campos mínimos típicos |
| **Fonte oficial** | URL canônica |

**Níveis de prontidão do atlas**

| Nível | Significado |
|-------|-------------|
| **A** | Formato oficial estável, bem documentado, implementável |
| **B** | Oficial, mas regional / multi-formulário / em transição |
| **C** | Rede fraca ou reporte não padronizado; arquivo local + convenção AstroCitizen |
| **D** | Educacional / interno apenas |

---
