---
chunk_id: docs-entrada-010
source_id: docs-entrada
path: docs/ENTRADA_OBSERVACOES_POR_PO.md
title: 8. Decisões fechadas neste documento
trust_tier: T3
lang: pt
topics: ["entrada", "channels"]
po_id: null
network: solar
pipeline_stage: help
token_estimate: 218
chunk_hash: "sha256:5b0c4f65003a3a7fad09cde74007b1066e651a20a2453be24c631709057066d8"
corpus_version: 0.1.0-kb1
---

## 8. Decisões fechadas neste documento

1. **Observação ≠ só imagem.** Visual, rádio, timing e logs são entradas de primeira classe.  
2. **PO-* escolhe canais**, não inventa formato de BD novo — reutiliza Observation / Artifact / AnalysisProduct.  
3. **Produto mínimo** (RN-043) valida se a entrada foi suficiente antes do export.  
4. **Safety solar** é entrada obrigatória (já no CLI sunspots); GUI deve espelhar.  
5. Epic de canais prioritários (§7) fechado; fila pós-UX (astrometria→Arquivo→AC-161→AC-152→AC-190) ✅; polish ContextBar opcional.

---

## 9. Relação com o atlas de redes

A entrada (este doc) é **a montante** do [ATLAS_REPORTE_OBSERVACOES.md](atlas/ATLAS_REPORTE_OBSERVACOES.md):

- Aqui: *como o humano entrega dados ao AstroCitizen*  
- Atlas: *como o AstroCitizen entrega dados à rede*

Ambos são necessários por PO-*.

---

## Histórico

| Ver. | Data | Nota |
|------|------|------|
| 1.0 | 2026-07-21 | Mapa inicial 9 canais + tabela de todos os PO-* do catálogo / programas |
| 1.1 | 2026-07-22 | Epic §7 canais 1-7 fechado (incl. especialidades P4) |
