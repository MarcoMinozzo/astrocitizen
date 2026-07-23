---
chunk_id: atlas-reporte-005
source_id: atlas-reporte
path: docs/atlas/ATLAS_REPORTE_OBSERVACOES.md
title: 3.10 Redes solares
trust_tier: T3
lang: pt
topics: ["networks", "export"]
po_id: null
network: aavso
pipeline_stage: help
token_estimate: 292
chunk_hash: "sha256:4b678211f083c76ec5a8e584ce5058bc2d2c071695688683c2cbf39d328bcec2"
corpus_version: 0.1.0-kb1
---

## 3.10 Redes solares

| | |
|--|--|
| **PO-*** | E03, E04, B06, I01 |
| **Canal** | Múltiplos (AAVSO Solar, BAA, ALPO, SILSO/SIDC para contagens, rádio clubs…) |
| **Nível** | B–C |

## Política AstroCitizen (v1)

- Persistência interna completa (imagens, timestamps, instrumentação, safety checklist)  
- Exporters específicos por rede solar ativados sob demanda quando a rede alvo for escolhida no programa  
- Contagem de manchas / SID: seguir formulários da rede escolhida na implementação  

---

## 3.11 Programas sem rede externa (arquivo AstroCitizen)

| PO-* | Produto mínimo interno | Formato sugerido no BD/artefato |
|------|------------------------|--------------------------------|
| A04 clusters UBVRI | Tabela mag/cores + FITS calibrados | CSV + FITS |
| A07/A08 rápida / asteroseis | Série temporal | Tabela tempo-magnitude |
| B04–B08 | Espectro 1D / lab | FITS 1D (+ BeSS keywords se aplicável) |
| E01–E02, E05–E06, F* | Imaging / logs | FITS/TIFF + metadados sessão |
| H01 polarimetria | Stokes / pol.% | Tabela + FITS |
| I02–I04 rádio | Potência vs tempo / espectro | Tabela/HDF5 |
| J* calibração | Masters + métricas CCD | FITS masters + tabela ruído/ganho |
| K* educação | Relatório de lab | PDF/Markdown + dataset |

**Nível:** C–D — ainda assim **obrigatório** gravar no BD (RN-110).

---
