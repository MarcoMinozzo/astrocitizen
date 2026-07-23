---
chunk_id: docs-entrada-003
source_id: docs-entrada
path: docs/ENTRADA_OBSERVACOES_POR_PO.md
title: B — Espectroscopia
trust_tier: T3
lang: pt
topics: ["entrada", "channels"]
po_id: null
network: bess
pipeline_stage: help
token_estimate: 278
chunk_hash: "sha256:e87c0faa08c08a89ad2ffa4483f5bbc11b3ab9b36ab0d14731e70a5e3f3a42d3"
corpus_version: 0.1.0-kb1
---

## B — Espectroscopia

| PO | Como o utilizador fornece | Canais | Payload mínimo | Produto | Estado |
|----|---------------------------|--------|----------------|---------|--------|
| **B01** Slit geral | Captura/import 2D; marca trace; calib λ (linhas / lâmpada) | IN-SPEC, IN-CAP | FITS 2D + λ | `spectrum_1d` | parcial |
| **B02** Be/BeSS | Igual B01 + object Be + keywords BeSS | IN-SPEC | FITS 1D BSS_* | spectrum → BeSS | parcial (export) |
| **B03** Novae/ARAS | Série de espectros no tempo | IN-SPEC | vários 1D | série espectral | desenho |
| **B04** Class. MK | Espectro 1D + escolha de templates | IN-SPEC, IN-LOG | 1D + tipo | classificação | desenho |
| **B05** RV educ. | Espectro + linhas de calibração | IN-SPEC | 1D + λ ref | RV table | desenho |
| **B06** Spec solar | Safety checklist + espectro solar | IN-LOG + IN-SPEC | safety + 1D/2D | linhas solares | desenho |
| **B07** Echelle | Import ordem(s) echelle | IN-SPEC | multi-order FITS | spectrum | ✅ `import echelle` |
| **B08** Lab spectro | Flats / lâmpada / testes (sem alvo céu) | IN-CAP, IN-IMP | calib frames | métricas resolução | desenho |
