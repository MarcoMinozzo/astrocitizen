# Sprint — Medida astrometria GUI (AC-111 bridge)

**Data:** 2026-07-22  
**Estado:** concluido  
**Base:** [SPRINT_PLATESOLVE_AC110.md](SPRINT_PLATESOLVE_AC110.md), CLI `analyze astrometry`

## Entrega

Grupo **Medir astrometria** em Analisar > Blink / Astrom:

- FITS (path preenchido apos plate-solve via `wcs_uri`)
- X/Y pixel + designation/band + nonsidereal
- Hints tan-plane (RA0/Dec0/scale/PA) se sem WCS
- Persistencia via `MeasureAstrometry` + log + UUID em Curvas

## DoD

- [x] Bridge GUI espelha CLI
- [x] Ligacao pos plate-solve (path WCS)
- [x] Docs DESKTOP_UI + este sprint
