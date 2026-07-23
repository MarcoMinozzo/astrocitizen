# Sprint EXP-COBS — Export + Revisar campos (PO-A10)

**Data:** 2026-07-23  
**Estado:** concluido  
**Atlas:** EXP-COBS-ICQ (P3) · `ATLAS_REPORTE_OBSERVACOES.md` §3.5

## Entregas

1. `contribution/cobs.py` — `#TYPE=ASTROCITIZEN_COBS` + CSV + UT ICQ `YYYY MM DD.DD`
2. AC-141 `_validate_cobs` + CLI `contribute cobs` / `validate --network cobs`
3. GUI Contribuir: tab **COBS** + **Revisar campos**
4. Prefill a partir de `visual_log` / `light_curve` (+ site → location)

## Fora deste slice

- Encoder ICQ 80 colunas fixas
- Submit HTTP COBS
- Produto dedicado `comet_observation` (coma/DC nativos)

## DoD

- [x] Export form-driven ou a partir de visual_log
- [x] Validacao bloqueia incompleto
- [x] CSV para paste no portal COBS
- [x] Testes
