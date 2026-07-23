# Sprint — AC-101 Calibração λ

**Data:** 2026-07-23  
**Estado:** concluido  
**Depende:** AC-100  
**Seguinte:** AC-102 (EW / medidas de linha formal)

## Objetivo

Calibrar o eixo de comprimento de onda além do linear de 2 pontos:
polinómio (grau 1–3) por pares `pix:nm`, ou matching de lâmpada Neon/Hg.

## Entregas

1. `analysis/wavelength_calib.py` — fit, picos, catalogos, `CalibrateWavelength`
2. Headers `AC_WDEG` / `AC_WCk` / `AC_WRMS` no FITS 1D
3. `load_spectrum_arrays` (AC-106) lê a solução polinomial
4. CLI `analyze spectrum-calibrate` + `--wave-pairs` em `analyze spectrum`
5. GUI Analisar → Espectro: wave pairs + botão calibrar
6. Testes `tests/test_wavelength_ac101.py`

## Uso

```bash
# Pares manuais (polinomio)
astrocitizen analyze spectrum-calibrate --product <uuid> \
  --wave-pairs "10:585.25,80:609.62,140:640.22" --degree 2

# Lamp Neon (mesmo n_pix que a ciencia) + seed linear
astrocitizen analyze spectrum-calibrate --fits-uri file:///sci_1d.fits \
  --lamp-uri file:///lamp_1d.fits --catalog neon --wave0 580 --wave1 700
```

## Fora deste slice

- Distortion 2D / re-extracção com curva do trace
- Atlas ThAr completo / ISIS
- Persistência dedicada `wavelength_solution` (AC-103 pode formalizar)

## DoD

- [x] Poly fit + RMS
- [x] Lamp Neon/Hg matching
- [x] Produto spectrum_1d recalibrado
- [x] Compatível com spectrum-report
- [x] CLI + GUI + testes + backlog
