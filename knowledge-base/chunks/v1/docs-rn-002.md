---
chunk_id: docs-rn-002
source_id: docs-rn
path: docs/ESCOPO_GERAL_E_REGRAS_DE_NEGOCIO.md
title: 2.1 Em escopo
trust_tier: T3
lang: pt
topics: ["rules", "product"]
po_id: null
network: aavso
pipeline_stage: help
token_estimate: 412
chunk_hash: "sha256:82d8c20c3cdf8bb750398b9815e6b74b3f7ff90e94d4dbf96f53a166ba51e157"
corpus_version: 0.1.0-kb1
---

## 2.1 Em escopo

| Capacidade | Descrição |
|------------|-----------|
| **Catálogo / resolução de alvos** | Identificar objetos (nome, coordenadas, tipo) via serviços e catálogos. |
| **Efemérides observacionais** | Posição, altitude/azimute, nascer/ocaso, janelas de visibilidade, eventos (trânsito, ocultação, oposição, etc.) para o **site** e o **intervalo de tempo** escolhidos. |
| **Meteorologia do site** | Condições atuais e previsão no local de observação (nuvens, vento, umidade, precipitação, temperatura, seeing estimado quando disponível). |
| **Perfis de site** | Locais de observação com coordenadas, altitude, fuso, horizonte/obstáculos opcionais. |
| **Inventário de equipamento** | Montagens, câmeras, focuser, filtros, espectrógrafos, etc., com estado e compatibilidade. |
| **Planejamento de equipamento** | Escolher/validar o conjunto instrumental para cada observação ou programa do dia. |
| **Programas observacionais** | Campanhas científicas cidadãs (variáveis, NEO, ARAS, IOTA, solar, …) com regras, alvos e entregáveis. |
| **Programa diário** | Agenda do dia/noite: sequência de blocos observacionais derivados dos programas ativos + efemérides + meteo + equipamento. |
| **Execução / aquisição** | Controle de instrumentos (Alpaca/udrv) conforme o plano, quando o usuário iniciar a sessão. |
| **Registro de observações** | Metadados, FITS/dados brutos, log de sessão, condições meteo no momento, equipamento usado. |
| **Análise** | Redução e medidas conforme o tipo de programa (fotometria, espectro, astrometria, timing, …). |
| **Gestão de programas** | Criar, ativar, pausar, priorizar, arquivar programas; acompanhar progresso e contribuições a redes. |
| **Exportação / reporte** | Formatos exigidos pelas redes cidadãs (AAVSO, MPC, IOTA, ARAS/BeSS, etc.). |

## 2.2 Fora de escopo (negócio)

- Ensino teórico de astrofísica como produto principal.  
- Projeto civil / CAD de observatório.  
- Previsão meteorológica global genérica sem vínculo ao site de observação.  
- Substituição obrigatória de todos os softwares especializados externos (a plataforma **orquestra e integra**; pode importar previsões IOTA, etc.).  
- Redistribuição de drivers proprietários.

---
