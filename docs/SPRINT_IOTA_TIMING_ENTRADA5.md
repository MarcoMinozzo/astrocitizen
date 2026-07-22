# Sprint — Timing IOTA (ENTRADA #5 / AC-120)

Import previsao + registo de contactos D/R. Video/SER adiado.

## Entregas

| Item | Detalhe |
|------|---------|
| Domain | `observatory/occultation.py` |
| Produtos | `occultation_prediction`, `occultation_timing` |
| CLI | `import prediction` · `observe occultation` |
| GUI | nav **Timing** |

## Formato previsao (TXT)

```
EventID: 2026Jul22_Demo
Star: TYC 1234-5678-1
Asteroid: (704) Interamnia
EventUTC: 2026-07-22T03:15:00Z
Duration_s: 12.5
```

Ou CSV com cabecalho `event_id,star,asteroid,event_utc,...`.

## Uso

```bash
astrocitizen import prediction --path pred.txt
astrocitizen observe occultation --event EV99 --star "HIP 123" --asteroid "(1) Ceres" \
  --result positive --d-time 2026-07-22T04:00:10Z --r-time 2026-07-22T04:00:22Z
```

## Checklist

- [x] Parse TXT/CSV
- [x] Import product + artifact
- [x] Timing contacts
- [x] GUI Timing + export pack
- [ ] Video/SER ingest (proxima onda)
