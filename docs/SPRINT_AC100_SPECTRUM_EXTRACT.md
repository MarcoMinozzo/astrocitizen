# Sprint — AC-100 Extração espectro 1D

**Data:** 2026-07-23  
**Estado:** concluido  
**Depende:** E6 (calib frames opcional), esqueleto PO-B01  
**Seguinte:** AC-101 (calibração λ além do linear)

## Objetivo

Passar do esqueleto “soma espacial” para uma **extração slit utilizável**:
auto-localização do trace, subtração de céu, métricas e produto `spectrum_1d` estável.

## Entregas

1. `find_trace_peak` / `spatial_profile` / `extract_trace` (+ sky)
2. `ExtractSpectrum1D` método `slit_sum_v1` (headers ACMETHOD, TRACE_Y, SKYSUB, AC_SNR)
3. CLI: `--auto-trace`, `--no-sky`, `--sky-offset`, `--sky-width` (`--trace-y` opcional)
4. GUI Analisar → Espectro: checkboxes Auto-trace / Subtrair céu
5. Testes `tests/test_spectrum_ac100.py`

## Fora deste slice (AC-101+)

- Solução λ por lâmpada / polinómio / atlas
- Extração óptima (Horne) / curvatura do trace
- Rectificação 2D completa

## Uso

```bash
astrocitizen analyze spectrum --fits-uri file:///path/2d.fits --auto-trace \
  --wave0 400 --wave1 700

astrocitizen analyze spectrum --fits-uri file:///path/2d.fits --trace-y 256 \
  --half-width 4 --no-sky
```

## DoD

- [x] Auto-trace + sky subtraction
- [x] Produto `spectrum_1d` + pontos no BD
- [x] CLI + GUI
- [x] Testes sintéticos
- [x] Backlog / docs
