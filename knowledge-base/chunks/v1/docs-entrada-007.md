---
chunk_id: docs-entrada-007
source_id: docs-entrada
path: docs/ENTRADA_OBSERVACOES_POR_PO.md
title: J — Calibração / site
trust_tier: T3
lang: pt
topics: ["entrada", "channels"]
po_id: null
network: null
pipeline_stage: help
token_estimate: 352
chunk_hash: "sha256:05b7be168b2a1b33a07b42857c6c27f61678dd84fa7774fe80bab45b2e7fa8b2"
corpus_version: 0.1.0-kb1
---

## J — Calibração / site

| PO | Como o utilizador fornece | Canais | Payload mínimo | Produto | Estado |
|----|---------------------------|--------|----------------|---------|--------|
| **J01** CCD gain/noise | Bias/dark/flat de laboratório | IN-CAP, IN-IMP | masters set | calibration metrics | parcial (masters) |
| **J02** Seeing/FWHM | Lights + medida FWHM (auto) | IN-CAP, IN-IMP | FITS | seeing series | desenho (template) |
| **J03** Masters rotina | Igual J01 campanha | IN-CAP, IN-IMP | bias/dark/flat | CalibrationMaster | parcial |
| **J04** Foco/colimação | Frames de teste + notas | IN-CAP, IN-LOG | FITS + log | focus report | desenho (template) |
| **J05** Meteo site | Pull API **ou** entrada manual thresholds/snapshot | IN-API, IN-LOG | meteo JSON | meteo snapshot | parcial (Noite) |

## K — Educação

| PO | Como o utilizador fornece | Canais | Payload mínimo | Produto | Estado |
|----|---------------------------|--------|----------------|---------|--------|
| **K01** Lab CCD | Dataset exemplo + passos guiados | IN-IMP, IN-LOG | FITS lab + workbook | lab report | desenho |
| **K02** Mini espectro | Igual B01 em modo lab | IN-SPEC | 2D/1D | lab spectrum | desenho (template) |
| **K03** Mini rádio | Igual I* em modo lab | IN-RAD | CSV | lab radio | desenho |
| **K04** Observatório escolar | Checklist projecto (não noite única) | IN-LOG | formulário projecto | project dossier | desenho (template) |

> Templates **J02, J04, K02, K04** estão em PROGRAMAS_OBSERVACIONAIS mas podem faltar no `program_templates.json` — incluir no seed quando se implementar o canal.

---
