# Sprint — Observar: Solar + Log visual (ENTRADA #4)

Superficie GUI **Observar** com abas Solar (PO-E03) e Log visual (PO-F03).

## Entregas

| Item | Detalhe |
|------|---------|
| GUI | `desktop/observe_panel.py` · nav **Observar** |
| Solar | checklist safety + CountSunspots + export |
| Visual | `LogVisualObservation` · produto `visual_log` |
| CLI | `observe log-visual --object ... --description ...` |
| Workflow | PO-F03 |

## Uso

```bash
astrocitizen observe log-visual --object M42 --description "visivel em binoculos" --conditions "ceu limpo"
```

GUI: **Observar** → Solar (marcar 3 checks + FITS) ou Log visual (objecto + descricao).

## Sequencia seguinte (ENTRADA #5)

Timing/IOTA import previsao + video (PO-D01).
