---
chunk_id: docs-rn-008
source_id: docs-rn
path: docs/ESCOPO_GERAL_E_REGRAS_DE_NEGOCIO.md
title: 6.8 Análise
trust_tier: T3
lang: pt
topics: ["rules", "product"]
po_id: null
network: null
pipeline_stage: help
token_estimate: 381
chunk_hash: "sha256:64bf12a383a35fd6f276904d343a82d794476cb93783e6b425647c2e2bf6dae0"
corpus_version: 0.1.0-kb1
---

## 6.8 Análise

| ID | Regra |
|----|--------|
| RN-070 | A análise disponível depende do **tipo do ProgramaObservacional** / técnica do bloco (fotometria, espectro, astrometria, timing, imaging…). |
| RN-071 | Todo ProdutoAnalise referencia as Observacoes de origem e os parâmetros de redução. |
| RN-072 | Reprocessar gera nova versão do produto; a versão “publicável” é marcada explicitamente pelo observador. |
| RN-073 | Análise pode ocorrer dias após a aquisição; o ProgramaDiario histórico permanece consultável. |

## 6.9 Contribuição e redes

| ID | Regra |
|----|--------|
| RN-080 | Exportação para rede só é permitida se o ProdutoAnalise atender o **produto mínimo** do programa (RN-043). |
| RN-081 | Cada ContribuicaoRede registra status `rascunho` \| `validado` \| `exportado` \| `enviado` \| `rejeitado`. |
| RN-082 | Credenciais de redes não ficam em texto claro no repositório de dados do projeto; uso de segredo local do usuário. |
| RN-083 | Formatos, formulários e campos de reporte seguem o **atlas interno** `docs/atlas/ATLAS_REPORTE_OBSERVACOES.md` (fontes oficiais). |

## 6.10 Hardware e execução

| ID | Regra |
|----|--------|
| RN-090 | Comandos de slew/exposição só ocorrem com confirmação de Sessao ativa (exceto modo diagnóstico). |
| RN-091 | Simulador é equivalente funcional para planejamento/treino/CI; Observacoes simuladas são flagadas `simulada=true`. |
| RN-092 | Falha de instrumento marca o bloco como `falhou` e **não** avança automaticamente para o próximo sem política do programa (default: pausar e alertar). |

## 6.11 Integridade e auditoria

| ID | Regra |
|----|--------|
| RN-100 | Ações que alteram ProgramaDiario, Programas, Inventário ou exclusões geram entrada de log auditável. |
| RN-101 | Preferências e limiares (altitude mínima, meteo) são por Site e/ou Programa, com defaults da plataforma. |
