---
chunk_id: docs-entrada-004
source_id: docs-entrada
path: docs/ENTRADA_OBSERVACOES_POR_PO.md
title: C — Astrometria / NEO / SN
trust_tier: T3
lang: pt
topics: ["entrada", "channels"]
po_id: null
network: mpc
pipeline_stage: help
token_estimate: 340
chunk_hash: "sha256:326e4660371d4d7fa84baf672a5ea5d8d3508eb67c406841b8bb030e8a7aa2d0"
corpus_version: 0.1.0-kb1
---

## C — Astrometria / NEO / SN

| PO | Como o utilizador fornece | Canais | Payload mínimo | Produto | Estado |
|----|---------------------------|--------|----------------|---------|--------|
| **C01** NEO/MPC | Captura/import FITS; plate-solve; clica objecto | IN-CAP, IN-IMP, IN-API | FITS+WCS + (x,y) | `astrometry` → ADES | parcial |
| **C02** Follow-up | Igual C01 + modo não-sideral / taxa | IN-CAP | FITS + rates | astrometry | parcial |
| **C03** SN/TNS | Par new/ref (blink); confirma candidato | IN-IMP, IN-CAP | 2 FITS | `blink_candidate` → TNS | parcial |
| **C04** Cometas astrom | Igual C01 + tracking cometa | IN-CAP | FITS + ephem | astrometry | desenho |
| **C05** Recuperação | Import ephem Horizons + medida | IN-API, IN-IMP | ephem + FITS | astrometry | desenho |

## D — Ocultações / timing

| PO | Como o utilizador fornece | Canais | Payload mínimo | Produto | Estado |
|----|---------------------------|--------|----------------|---------|--------|
| **D01** Occ. asteróide | Import previsão IOTA + vídeo/série + GPS time | IN-PRED, IN-VID, IN-TAB | pred + LC timing | timing pack → IOTA | ✅ pred+timing+video/LC |
| **D02** Lunar/graze | Vídeo + station + contact times | IN-VID, IN-LOG | vídeo + contacts | timing | desenho |
| **D03** Mutuas | Timing + efemérides satélites | IN-TAB, IN-LOG | contact times | timing | desenho |
| **D04** Duplas occ. | Vídeo + análise de eventos | IN-VID | vídeo + measures | timing + dupla | desenho |
