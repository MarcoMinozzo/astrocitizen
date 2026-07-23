---
chunk_id: docs-entrada-001
source_id: docs-entrada
path: docs/ENTRADA_OBSERVACOES_POR_PO.md
title: Introduction
trust_tier: T3
lang: pt
topics: ["entrada", "channels"]
po_id: null
network: iota
pipeline_stage: help
token_estimate: 512
chunk_hash: "sha256:c02deba0339fb05b5b88473889e58a9851b1fc10974595d68a1c862231ee0d8e"
corpus_version: 0.1.0-kb1
---

## Introduction

# Entrada de observações por programa (PO-*)

**Status:** ✅ epic de canais prioritários fechado (2026-07-22) — ver §7  
**Data:** 2026-07-21 (desenho); 2026-07-22 (fecho engenharia 1–7)  
**Fontes:** [PROGRAMAS_OBSERVACIONAIS.md](PROGRAMAS_OBSERVACIONAIS.md), [atlas/ATLAS_REPORTE_OBSERVACOES.md](atlas/ATLAS_REPORTE_OBSERVACOES.md), [MODELO_DADOS_V1.md](MODELO_DADOS_V1.md), [WORKFLOWS.md](WORKFLOWS.md), catálogo `program_templates.json`  
**Mandato:** para **cada** PO-* definir *como* o utilizador fornece a informação observacional à plataforma — não só o formato de export.

---

## 1. Princípio

Não há 50 ecrãs distintos. Há **canais de entrada reutilizáveis** (padrões). Cada PO-* escolhe:

1. **Canal primário** de aquisição / ingestão  
2. **Metadados obrigatórios** (formulário / CLI / headers)  
3. **Produto mínimo** interno  
4. **Export** (rede), quando aplicável  

```
Canal de entrada  →  Observation + Artifact(s)  →  AnalysisProduct  →  Rede
```

Uma observação pode ter **zero imagens** (visual, rádio, timing puro) ou **muitos** FITS (fotometria, stack).

---

## 2. Canais partilhados (padrões de entrada)

| ID | Canal | O que o utilizador faz | Artefacto típico | Superfície alvo |
|----|-------|------------------------|------------------|-----------------|
| **IN-CAP** | Captura hardware | Sessão → expor (sim / Alpaca / udrv) | FITS 2D | GUI Sessão (wizard) + CLI `session capture` |
| **IN-IMP** | Import ficheiros | Arrasta / selecciona FITS, SER, AVI, CSV, HDF5… | ficheiro → ArtifactStore URI | GUI **Import** + CLI `import fits` (FITS feito; SER/CSV depois) |
| **IN-TAB** | Tabela / série | Cola ou importa CSV de fotometria, timing, rádio | CSV / pontos no BD | GUI Editor de série + CLI |
| **IN-LOG** | Log estruturado | Preenche formulário (visual, solar count, safety) | JSON + texto | GUI formulário PO-* |
| **IN-VID** | Vídeo / lucky | Importa SER/AVI ou pasta de frames | SER/AVI/FITS cube | GUI Imaging + pipeline stack |
| **IN-SPEC** | Espectro | Importa 2D (slit) ou 1D já extraído | FITS 2D/1D | GUI Espectro + CLI `analyze spectrum` |
| **IN-RAD** | Rádio | Importa potência vs tempo / espectro RF | CSV/HDF5/WAV | GUI Rádio (paralelo) |
| **IN-API** | Serviço externo | Confirma pull (meteo, efemérides, plate-solve) | JSON / FITS+WCS | Noite / analyze (já parcial) |
| **IN-PRED** | Previsão / alerta | Importa ficheiro de campanha (IOTA, µFUN, NEO) | XML/CSV/TXT | GUI Campanha |

**Regra:** todo canal grava `Observation` (metadados) + zero ou mais `artifacts`. Produtos científicos vivem em `analysis_products` / `measurement_points`.

---
