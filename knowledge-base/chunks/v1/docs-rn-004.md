---
chunk_id: docs-rn-004
source_id: docs-rn
path: docs/ESCOPO_GERAL_E_REGRAS_DE_NEGOCIO.md
title: 5. Fluxo de negócio principal (dia a dia)
trust_tier: T3
lang: pt
topics: ["rules", "product"]
po_id: null
network: null
pipeline_stage: help
token_estimate: 257
chunk_hash: "sha256:fe284d0be14e71634c20ddd384f6c1fc56faa86768afd8401637ce0af654cb58"
corpus_version: 0.1.0-kb1
---

## 5. Fluxo de negócio principal (dia a dia)

```
[Site] + [Programas ativos]
        ↓
[Efemérides] + [Meteo do site] + [Inventário de equipamento]
        ↓
   Planejar Programa Diário
        ↓
   Validar viabilidade (céu + meteo + equipamento)
        ↓
   Executar Sessão (opcional / quando houver hardware)
        ↓
   Registrar Observações
        ↓
   Analisar → Produtos
        ↓
   Atualizar Programas + Exportar para redes
```

O sistema deve permitir usar só o trecho de **planejamento** (sem hardware) e só o trecho de **análise** (dados já adquiridos).

---

## 6. Regras de negócio

Convenção: **RN-XXX** — obrigatórias salvo indicação “desejável”.

## 6.1 Site e tempo

| ID | Regra |
|----|--------|
| RN-001 | Toda efeméride, meteo e programa diário são relativos a um **Site** explícito. Não existe “céu genérico” sem local. |
| RN-002 | O Site ativo pode ser alterado; ao mudar o Site, efemérides e viabilidade do ProgramaDiario devem ser **recalculadas**. |
| RN-003 | Tempos de observação, headers e logs usam escala de tempo explícita (UTC obrigatório nos dados; hora local apenas na UI). |
| RN-004 | Datas do ProgramaDiario referem-se à **noite civil** do Site (configurável: crepúsculo astronômico / horário local de início). |
