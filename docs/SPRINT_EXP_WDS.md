# Sprint EXP-WDS — Export + Revisar campos (PO-G01)

**Data:** 2026-07-23  
**Estado:** concluido  
**Atlas:** EXP-WDS (P2) · `ATLAS_REPORTE_OBSERVACOES.md` §3.9

## Entregas

1. `contribution/wds.py` — formato `#TYPE=ASTROCITIZEN_WDS` + CSV gemelo
2. CLI `contribute wds --product` (gate AC-141)
3. GUI Contribuir: tab **WDS** + **Revisar campos**
4. Prefill a partir de `double_measure` (site → observatory)

## Fora deste slice

- Submit HTTP USNO (manual)
- R3 Revisar campos TNS/ExoClock/BeSS/IOTA
- COBS

## DoD

- [x] Export a partir de LogDoubleMeasure
- [x] Validacao AC-141 bloqueia incompleto
- [x] CSV + texto para paste USNO
- [x] Testes
