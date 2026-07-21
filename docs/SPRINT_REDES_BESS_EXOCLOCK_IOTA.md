# Sprint redes P2 - BeSS + ExoClock + IOTA

**Data:** 2026-07-21  
**Meta:** exporters P1 restantes (espectroscopia, tramsitos, ocultacoes)  
**PO-*:** B02/B03 (BeSS), A05 (ExoClock), D01 (IOTA)

## DoD

1. **BeSS** - FITS 1D com keywords BSS_* / OBJNAME / DATE-OBS (+ WCS espectral)
2. **ExoClock** - ficheiro LC txt (BJD_TDB, flux, err, airmass) a partir de measurement_points
3. **IOTA** - pacote regional (TXT estilo IOTA-ES + meta JSON + LC csv)
4. CLI `contribute bess|exoclock|iota` + tabs GUI Contribute
5. network_submissions status draft / dry_run (upload portal = manual)
6. Testes sem rede

## Canais (sem API HTTP)

| Rede | Upload |
|------|--------|
| BeSS | portal basebe.obspm.fr |
| ExoClock | exoclock.space/upload |
| IOTA | hub regional / SODIS / e-mail |

## Fora

- Checker BeSS completo / validacao admins
- Plate-solve / tempos GPS reais IOTA
- Import previsao OccultWatcher (AC-120)
