---
chunk_id: docs-entrada-008
source_id: docs-entrada
path: docs/ENTRADA_OBSERVACOES_POR_PO.md
title: 5. Superfícies de UI necessárias (agrupadas)
trust_tier: T3
lang: pt
topics: ["entrada", "channels"]
po_id: null
network: solar
pipeline_stage: help
token_estimate: 302
chunk_hash: "sha256:24f5dba4f1c4b2d853831207a408df375466e2ade19d2da6b26e015dd2999e03"
corpus_version: 0.1.0-kb1
---

## 5. Superfícies de UI necessárias (agrupadas)

Em vez de 50 apps, **7 superfícies**:

| Superfície | Serve PO-* | Entrada |
|------------|------------|---------|
| **Sessão / Captura** | A, B, C, E, F, G, H, J | IN-CAP |
| **Importador** | quase todos | IN-IMP / IN-VID / IN-RAD |
| **Fotometria** | A* | pontos, comp stars |
| **Espectro** | B* | trace, λ |
| **Astrometria / Blink** | C* | solve + click |
| **Timing / Occultation** | D* | pred + vídeo + contacts |
| **Log / Safety / Visual / Solar count** | E03–04, F03–04, G01 manual, K* | IN-LOG |

**Noite** (já existe) alimenta J05 + planeamento, não substitui captura científica.

---

## 6. CLI espelho (contrato mínimo a estabilizar)

| Família | Comandos alvo |
|---------|----------------|
| Import genérico | `astrocitizen import fits\|csv\|ser\|radio …` |
| Captura | `session capture` (existe) |
| Fotometria | `analyze photometry` (existe) |
| Espectro | `analyze spectrum` (existe) |
| Astrometria | `analyze plate-solve` + `astrometry` (existe) |
| Blink | `analyze blink` (existe) |
| Solar | `analyze sunspots` (existe) |
| Visual log | `observe log-visual` |
| Rádio | `import radio` (CSV/HDF5) |
| Occultation | `import prediction` · `observe occultation` |
| Especialidades P4 | `import echelle` · `import speckle` · `import polar` |

---
