---
chunk_id: docs-rn-005
source_id: docs-rn
path: docs/ESCOPO_GERAL_E_REGRAS_DE_NEGOCIO.md
title: 6.2 Efemérides e dados astronômicos
trust_tier: T3
lang: pt
topics: ["rules", "product"]
po_id: null
network: mpc
pipeline_stage: help
token_estimate: 348
chunk_hash: "sha256:1bf02872841e8ce54df517d6edb5745db112112ce885a91ee9f034c5df01a144"
corpus_version: 0.1.0-kb1
---

## 6.2 Efemérides e dados astronômicos

| ID | Regra |
|----|--------|
| RN-010 | Efemérides observacionais (Alt/Az, airmass, nascer/ocaso, trânsito meridiano) são calculadas com **Astropy** a partir de coordenadas/tempo/site. |
| RN-011 | Efemérides de corpos do Sistema Solar / NEOs usam serviços confiáveis (**Astroquery**/Horizons/MPC) quando a precisão orbital for necessária. |
| RN-012 | Um BlocoObservacional só pode ser marcado **viável no céu** se, na janela planejada, altitude ≥ limite do Programa (default configurável, ex.: 25°) e fora do Sol (exceto programas solares). |
| RN-013 | Eventos temporais críticos (ocultações, trânsitos) têm janela com margem de segurança definida pelo ProgramaObservacional. |
| RN-014 | Falha de rede ao obter efemérides remotas não apaga o plano: o sistema usa cache local ou marca o bloco como **efeméride indisponível**. |

## 6.3 Meteorologia do local

| ID | Regra |
|----|--------|
| RN-020 | O ProgramaDiario consulta **meteorologia do Site** (atual e/ou previsão para a janela da noite). |
| RN-021 | Condições mínimas (cobertura de nuvens, vento, precipitação, umidade) são limiares do Site ou do Programa; abaixo/acima do limiar o bloco fica **inviável por meteo** (não é excluído do histórico — fica justificado). |
| RN-022 | No início e no fim da Sessao, o sistema registra um snapshot de CondiçãoMeteo ligado às Observacoes. |
| RN-023 | Se a fonte meteo estiver indisponível, o usuário pode **sobrescrever manualmente** a decisão de observar (com flag `meteo_manual=true` no registro). |
| RN-024 | Meteo é sempre do **local de observação**, não de uma cidade arbitrária sem vínculo ao Site. |
