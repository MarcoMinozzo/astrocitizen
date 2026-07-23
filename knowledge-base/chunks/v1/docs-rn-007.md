---
chunk_id: docs-rn-007
source_id: docs-rn
path: docs/ESCOPO_GERAL_E_REGRAS_DE_NEGOCIO.md
title: 6.6 Programa diário e planejamento de observações
trust_tier: T3
lang: pt
topics: ["rules", "product"]
po_id: null
network: null
pipeline_stage: help
token_estimate: 333
chunk_hash: "sha256:37f7c67aae3b3eacad5e3e200136c3067043d9121a6606cd62a245c95584055c"
corpus_version: 0.1.0-kb1
---

## 6.6 Programa diário e planejamento de observações

| ID | Regra |
|----|--------|
| RN-050 | Existe no máximo **um ProgramaDiario vigente por Site e por data de noite**. |
| RN-051 | O ProgramaDiario é gerado/atualizado a partir de: programas ativos + efemérides + meteo + equipamento disponível. |
| RN-052 | O observador pode **editar** o programa diário (reordenar, incluir alvo manual, remover bloco) sem alterar a definição do ProgramaObservacional. |
| RN-053 | Cada bloco no diário tem status: `candidato` \| `agendado` \| `inviavel_ceu` \| `inviavel_meteo` \| `inviavel_equip` \| `em_execucao` \| `concluido` \| `pulado` \| `falhou`. |
| RN-054 | Blocos inviáveis permanecem visíveis com **motivo** (transparência do planejamento). |
| RN-055 | O planejamento pode ser feito **sem hardware** (modo planejamento puro). |
| RN-056 | Ao iniciar a Sessao, o sistema trava a versão do ProgramaDiario usada (snapshot) para rastreabilidade. |

## 6.7 Registro de observações

| ID | Regra |
|----|--------|
| RN-060 | Toda Observacao referencia: Site, tempo, Alvo (se houver), ConfiguraçãoInstrumental, Bloco/Programa (se houver), CondiçãoMeteo (se disponível). |
| RN-061 | Dados brutos (FITS etc.) não são alterados após a gravação; reduções geram **ProdutosAnalise** versionados. |
| RN-062 | Headers/metadados devem permitir reconstruir as condições da noite (site, equipamento, meteo, programa). |
| RN-063 | Observacoes podem existir **fora** de um ProgramaDiario (aquisição ad hoc), mas devem poder ser **associadas depois** a um programa. |
| RN-064 | Exclusão de Observacao é lógica (arquivamento); não apagar arquivos sem confirmação explícita. |
