# Sprint — Radio CSV/HDF5 (ENTRADA #6 / AC-160 / PO-I01)

Import serie potencia vs tempo (SDR/CSV ou HDF5).

## Entregas

| Item | Detalhe |
|------|---------|
| Domain | `observatory/radio.py` |
| Produto | `radio_timeseries` |
| Artefacto | `radio_timeseries` |
| Workflow | `PO-I01` |
| CLI | `import radio --path … [--freq MHz]` |
| GUI | nav **Radio** |

## CSV

Cabecalho `t_utc,power[,power_err]` (aliases: time/utc + intensity/flux/dbm/adu).

## HDF5

Requer `h5py`. Datasets `time`/`t_utc` + `power`/`intensity` (ou primeiros dois datasets).

## Uso

```bash
astrocitizen import radio --path sun.csv --freq 1420.4
```

## Checklist

- [x] Parse CSV
- [x] Import HDF5 (opcional h5py)
- [x] Observation + product + measurement_points
- [x] CLI + GUI
- [x] Workflow PO-I01

## Seguinte

ENTRADA #7 especialidades P4 fechado (`SPRINT_ESPECIALIDADES_ENTRADA7`). I02–I04 (espectro RF / drift) ficam em AC-161.
