---
chunk_id: docs-entrada-006
source_id: docs-entrada
path: docs/ENTRADA_OBSERVACOES_POR_PO.md
title: G / H — Duplas / polarimetria
trust_tier: T3
lang: pt
topics: ["entrada", "channels"]
po_id: null
network: null
pipeline_stage: help
token_estimate: 281
chunk_hash: "sha256:29be3ea27a8bda946dc7d62f437692907b6efbf907c447474d015d109c822b34"
corpus_version: 0.1.0-kb1
---

## G / H — Duplas / polarimetria

| PO | Como o utilizador fornece | Canais | Payload mínimo | Produto | Estado |
|----|---------------------------|--------|----------------|---------|--------|
| **G01** Duplas | Imagem **ou** micrómetro (ângulo/separação manual) | IN-IMP, IN-LOG | PA, sep, epoch | double_measure | ✅ `observe log-double` |
| **G02** Speckle | Cubo/speckle frames | IN-IMP | cube | speckle product | ✅ `import speckle` |
| **H01** Polarimetria | Frames em ângulos de polarizador | IN-CAP, IN-IMP | set polar | Stokes table | ✅ `import polar` |

## I — Rádio (não é imagem óptica)

| PO | Como o utilizador fornece | Canais | Payload mínimo | Produto | Estado |
|----|---------------------------|--------|----------------|---------|--------|
| **I01** Sol rádio | Série potência vs tempo (SDR/CSV) | IN-RAD | CSV/HDF5 | radio_timeseries | ✅ `import radio` |
| **I02** 21 cm | Espectro RF / waterfall | IN-RAD | espectro CSV | radio_spectrum | ✅ `import radio --kind spectrum` |
| **I03** Contínuo | Drift scan / pointing logs | IN-RAD, IN-LOG | scan CSV | radio_scan | ✅ `import radio --kind scan` |
| **I04** Lab VHF | Igual I01–I03 + notas de construção | IN-RAD, IN-LOG | série + lab notes | radio + lab_notes | ✅ `--lab-notes` |
