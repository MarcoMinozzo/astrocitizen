# Sprint — Especialidades P4 (ENTRADA #7 / AC-154)

Fecha o epic ENTRADA com canais de entrada para echelle, speckle e polarimetria.

## Entregas

| Item | Detalhe |
|------|---------|
| Domain | `observatory/specialties.py` |
| Produtos | `echelle_orders`, `speckle_cube`, `polarimetry_stokes` |
| Workflows | PO-B07, PO-G02, PO-H01 |
| CLI | `import echelle` · `import speckle` · `import polar` |
| GUI | nav **Especialidades** |

## Uso

```bash
astrocitizen import echelle --path orders.fits
astrocitizen import speckle --path cube.fits   # ou pasta / SER
astrocitizen import polar --path ./frames --angles angles.csv
```

CSV polar: `filename,angle_deg` (ou header FITS `POLANG`).

Stokes I/Q/U/P estimado quando existem frames perto de 0/45/90/135 deg (media ADU).

## Checklist

- [x] Import echelle multi-ext / pasta
- [x] Import speckle cubo / stack / video
- [x] Import polar + Stokes heuristico
- [x] CLI + GUI
- [x] Docs ENTRADA §7 completo

## Fora deste sprint (waves seguintes)

- Reducao echelle completa (extract por ordem + wavelength)
- Autocorrelacao / bispectrum speckle
- Calibracao polarimetrica instrumental
- I02–I04 radio espectro / drift (AC-161)
