---
chunk_id: docs-rn-006
source_id: docs-rn
path: docs/ESCOPO_GERAL_E_REGRAS_DE_NEGOCIO.md
title: 6.4 Equipamento e planejamento instrumental
trust_tier: T3
lang: pt
topics: ["rules", "product"]
po_id: null
network: aavso
pipeline_stage: help
token_estimate: 398
chunk_hash: "sha256:3a75946340659eff6eee3dc9cd406377b0a065036a53bada56ad6fe084de8216"
corpus_version: 0.1.0-kb1
---

## 6.4 Equipamento e planejamento instrumental

| ID | Regra |
|----|--------|
| RN-030 | Todo BlocoObservacional declara uma **ConfiguraçãoInstrumental** (ou herda a padrão do Programa). |
| RN-031 | O planejamento de equipamento valida: equipamento **disponível**, **compatível** com a técnica (ex.: espectrógrafo para espectroscopia) e **conectado/selecionável** no backend quando a sessão for instrumental. |
| RN-032 | Câmera: o usuário escolhe backend **udrv** ou **alpaca** (ou simulador); a escolha fica registrada na Observacao. |
| RN-033 | Montagem e focuser, quando exigidos pelo bloco, devem estar definidos na configuração; ausência gera status **equipamento incompleto**. |
| RN-034 | Mudança de equipamento no meio da Sessao gera novo trecho de log e metadados (não sobrescrever o anterior). |
| RN-035 | Inventário de equipamento é por observatório/usuário; itens podem ser marcados indisponíveis (manutenção). |

## 6.5 Programas observacionais

| ID | Regra |
|----|--------|
| RN-040 | Um ProgramaObservacional tem: tipo (domínio CS-*), objetivos, cadência, critérios de alvo, técnica, rede(s) de destino, prioridade, estado (`ativo` \| `pausado` \| `arquivado`). |
| RN-041 | Só programas **ativos** geram candidatos automaticamente no ProgramaDiario. |
| RN-042 | O sistema gerencia **múltiplos programas em paralelo**; conflitos de horário são resolvidos por **prioridade** e depois por janela de altitude/evento. |
| RN-043 | Cada programa define o **produto mínimo aceitável** (ex.: curva de luz diferencial; espectro λ-calibrado; astrometria MPC). |
| RN-044 | Programas ligados a redes (AAVSO, MPC, IOTA, ARAS…) devem conhecer o **formato de exportação** exigido. |
| RN-045 | Pausar um programa não apaga histórico nem Observacoes já feitas. |
| RN-046 | Todo ProgramaObservacional ativo deriva de um template **PO-*** do catálogo oficial (`PROGRAMAS_OBSERVACIONAIS.md`), ou é extensão documentada dele. |
| RN-047 | Novos tipos de programa fora do catálogo PO-* só entram após atualização formal desse catálogo. |
