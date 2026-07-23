---
chunk_id: atlas-reporte-006
source_id: atlas-reporte
path: docs/atlas/ATLAS_REPORTE_OBSERVACOES.md
title: 4. Matriz de implementação (exporters)
trust_tier: T3
lang: pt
topics: ["networks", "export"]
po_id: null
network: aavso
pipeline_stage: help
token_estimate: 265
chunk_hash: "sha256:43e70d9697baa4cde998664421bf4d7888f5dbabc1876455bedf0b0628a06ad8"
corpus_version: 0.1.0-kb1
---

## 4. Matriz de implementação (exporters)

| Exporter ID | Rede | Formato de saída | Prioridade produto |
|-------------|------|-----------------|--------------------|
| EXP-AAVSO-EXT | AAVSO | Extended text | P1 |
| EXP-AAVSO-VIS | AAVSO | Visual text | P2 |
| EXP-EXOCLOCK | ExoClock | LC txt (HOPS/AIJ-compatible) | P1 |
| EXP-MPC-ADES | MPC | ADES XML/PSV | P1 |
| EXP-COBS-ICQ | COBS | ICQ record / web fields | P3 |
| EXP-TNS-JSON | TNS | AT/Class JSON | P1 |
| EXP-BESS-FITS | BeSS | FITS 1D + BSS_* | P1 |
| EXP-IOTA-PACK | IOTA | Pacote regional (XLS/TXT+anexos) | P1 |
| EXP-WDS | WDS | Medida estruturada | P2 |
| EXP-LOCAL | — | Pacote AstroCitizen | P0 (sempre) |

---

## 5. Checklist genérico antes de exportar (RN-080)

1. Produto mínimo do PO-* atingido e versionado no BD  
2. Site, equipamento e tempo UTC consistentes  
3. Credenciais/códigos de observador presentes (OBSCODE, MPC code, TNS group…)  
4. Artefatos anexos exigidos pela rede (charts, LC plots, finding charts…)  
5. Validação contra schema/spec oficial quando existir (ADES XSD, BeSS checker, AAVSO parser…)  
6. Status `ContribuicaoRede`: rascunho → validado → exportado → enviado  

---
