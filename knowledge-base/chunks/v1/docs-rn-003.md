---
chunk_id: docs-rn-003
source_id: docs-rn
path: docs/ESCOPO_GERAL_E_REGRAS_DE_NEGOCIO.md
title: 3. Atores
trust_tier: T3
lang: pt
topics: ["rules", "product"]
po_id: null
network: aavso
pipeline_stage: help
token_estimate: 396
chunk_hash: "sha256:e423ea83cec3b006e996315079f7833dafacdb6efddb1377240763fc3340df41"
corpus_version: 0.1.0-kb1
---

## 3. Atores

| Ator | Papel |
|------|-------|
| **Observador** | Planeja, executa, registra e analisa observações. |
| **Gestor de programa** | (Pode ser o mesmo usuário) define campanhas, prioridades e critérios de sucesso. |
| **Sistema** | Calcula efemérides, consulta meteo/serviços, valida regras, agenda o programa diário. |
| **Instrumento** | Montagem, câmera, focuser, etc., via backends de hardware. |
| **Rede cidadã** | Destino externo de dados (AAVSO, MPC, …) — consumidor dos exports. |

Na versão inicial (usuário único / pequeno observatório), Observador e Gestor de programa são o mesmo perfil. Multi-usuário fica como evolução.

---

## 4. Entidades de domínio (modelo de negócio)

| Entidade | Descrição |
|----------|-----------|
| **Site** | Local de observação (`SiteProfile`: nome, lat, lon, alt, fuso, horizonte). |
| **CondiçãoMeteo** | Snapshot ou previsão associada a Site + instante/intervalo. |
| **Alvo** | Objeto celeste ou região (coordenadas, tipo, identificadores externos). |
| **Efeméride** | Quantidades observacionais do Alvo no Site em um tempo (Alt/Az, HA, airmass, eventos). |
| **Equipamento** | Item físico ou lógico (montagem, câmera, focuser, filtro, espectrógrafo…). |
| **ConfiguraçãoInstrumental** | Conjunto de Equipamentos usados juntos numa observação. |
| **ProgramaObservacional** | Campanha de longo prazo (tipo científico, regras, alvos, cadência, rede de destino). |
| **BlocoObservacional** | Unidade planejada: Alvo + técnica + exposição(ões) + equipamento + janela temporal. |
| **ProgramaDiario** | Conjunto ordenado de Blocos para uma data (e Site), com status. |
| **Sessao** | Execução real de (parte do) ProgramaDiario. |
| **Observacao** | Registro de uma aquisição/medida (dados + metadados + meteo + equipamento). |
| **ProdutoAnalise** | Resultado derivado (curva de luz, espectro 1D, astrometria, relatório de ocultação…). |
| **ContribuicaoRede** | Pacote exportado / enviado / a enviar para uma rede cidadã. |

---
