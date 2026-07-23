# Sprint — PO-G01 Duplas (AC-152)

**Data:** 2026-07-23  
**Estado:** concluido  
**Base:** ENTRADA G01, `LogVisualObservation` pattern

## Entregas

| Componente | Papel |
|------------|--------|
| `LogDoubleMeasure` | Observation + `double_measure` (PA/sep/epoch) |
| CLI | `observe log-double --object --pa --sep` |
| GUI | Observar → Duplas (PO-G01) |
| Workflow | PO-G01: plan → log_double_measure → review |

## Uso

```bash
astrocitizen observe log-double \
  --object "WDS 04184+2135" --pa 127.3 --sep 2.45 \
  --when 2026-07-23T02:15:00Z [--image ./pair.fits]
```

## Fora deste slice

- Auto PA/sep a partir de dois cliques / WCS
- Export WDS / EXP-WDS
- Speckle reduce (PO-G02)

## DoD

- [x] Dominio + validacao PA/sep
- [x] CLI + GUI Observar
- [x] Workflow + guide
- [x] Testes `test_double_g01.py`
- [x] ENTRADA / backlog AC-152
