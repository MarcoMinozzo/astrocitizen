---
chunk_id: docs-rn-009
source_id: docs-rn
path: docs/ESCOPO_GERAL_E_REGRAS_DE_NEGOCIO.md
title: 6.11b UX / plataforma (idioma e ajuda)
trust_tier: T3
lang: pt
topics: ["rules", "product"]
po_id: null
network: null
pipeline_stage: help
token_estimate: 440
chunk_hash: "sha256:cc5f4739e637e47b3fd9dc61cff06fedd284e791ce8c7279457c2f3664ccd2b2"
corpus_version: 0.1.0-kb1
---

## 6.11b UX / plataforma (idioma e ajuda)

| ID | Regra |
|----|--------|
| RN-120 | UI da app e da plataforma oferece tres linguas: portugues (`pt`), espanhol (`es`) e ingles (`en`). Lingua do SO (desktop) ou browser (SaaS) e detectada automaticamente. O utilizador pode fixar preferencia e ignorar a deteccao. Se a lingua detectada/preferida nao for suportada, usa-se **`en`**. Preferencia canonica: `auto` \| `pt` \| `es` \| `en`. |
| RN-121 | Existe **Ajuda** acessivel na UI (desktop e, no futuro, web) que orienta o uso por area (Noite, Observatorio, Programa, Analisar, Contribuir, Arquivo, Configurar). O conteudo da ajuda segue a lingua efectiva (RN-120). |

---

## 6.12 Persistência e bancos de dados

| ID | Regra |
|----|--------|
| RN-110 | Todo resultado observacional alimenta **banco(s) de dados**; arquivo sozinho não é estado final. |
| RN-111 | FITS/bruto imutável; reduções = novas versões de produto no BD. |
| RN-112 | Consultas de gestão e ciência usam o BD como fonte primária (artefatos são referenciados). |
| RN-113 | Snapshots de meteo/efemérides usados em decisões são persistidos. |
| RN-114 | Exclusão lógica + auditoria; purge físico só com política explícita. |
| RN-115 | Observações simuladas também entram no BD, marcadas e filtráveis. |
| RN-116 | Schema versionado com migrações. |

Detalhe: `PERSISTENCIA_E_BANCOS.md`.

## 7. Estados resumidos

## ProgramaObservacional

`rascunho` → `ativo` ⇄ `pausado` → `arquivado`

## ProgramaDiario

`rascunho` → `publicado` → `em_execucao` → `encerrado`

## BlocoObservacional

ver RN-053

## Observacao

`bruta` → `calibrada` → `analisada` → `publicavel` / `arquivada`

---

## 8. Requisitos de informação mínimos

## Programa diário (saída do planejamento)

Para cada bloco: alvo, janela UT, altitude prevista, airmass, status céu/meteo/equip, configuração instrumental, programa de origem, prioridade, notas.

## Registro de observação

Identificadores, tempos, site, meteo, equipamento/backend, arquivos de dados, vínculo a bloco/programa, flags (simulada, meteo_manual).

## Painel de gestão de programas

Lista de programas, estado, próxima janela útil, observações recentes, contribuições pendentes, alertas (meteo ruim, efeméride falhou, equipamento indisponível).

---
