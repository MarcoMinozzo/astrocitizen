# Sprint — Timing IOTA (ENTRADA #5 / AC-120 + IN-VID)

Import previsao + video/SER + LC CSV + contactos D/R + timesource.

## Entregas

| Item | Detalhe |
|------|---------|
| Domain | `observatory/occultation.py` |
| Produtos | `occultation_prediction`, `occultation_timing` |
| Artefactos | `video_ser` / `video_occ` / `occultation_lc` |
| CLI | `import prediction` · `observe occultation --video/--lc/--suggest-contacts` |
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

## LC CSV

Cabecalho `t_utc,signal` (aliases: time/utc + y/flux/intensity/adu).

## Uso

```bash
astrocitizen import prediction --path pred.txt
astrocitizen observe occultation --event EV99 --star "HIP 123" --asteroid "(1) Ceres" \
  --result positive --timesource GPS \
  --video event.ser --lc lc.csv --suggest-contacts
```

## Checklist

- [x] Parse TXT/CSV previsao
- [x] Import product + artifact
- [x] Timing contacts + timesource NTP|GPS|VTI|manual|PC
- [x] Video/SER ingest (artifact)
- [x] LC CSV + measurement_points + suggest D/R (AC-122 inicio)
- [x] GUI Timing + export pack
