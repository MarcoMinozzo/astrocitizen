# Sprint — Plate-solve / WCS (AC-110)

**Data:** 2026-07-21  
**Estado:** concluido

## Entregas

| Componente | Papel |
|------------|--------|
| `ports/platesolve.py` | `PlateSolvePort` + `PlateSolveResult` |
| `adapters/platesolve/` | `solve-field`, Nova API, `synthetic` |
| `analysis/platesolve.py` | Persistencia `wcs_solution` + FITS com WCS |
| CLI | `analyze plate-solve --backend auto\|solve-field\|nova\|synthetic` |
| Workflows | PO-C01/C02 incluem passo `plate_solve` |

## Uso tipico

```bash
# Offline / CI (hints obrigatorios)
astrocitizen analyze plate-solve --fits-uri file://... \
  --backend synthetic --ra-hint 180 --dec-hint 10 --scale-low 1 --scale-high 1

# Local (astrometry.net instalado)
astrocitizen analyze plate-solve --fits-uri file://... --backend solve-field \
  --ra-hint 180 --dec-hint 10 --radius 1

# Nova (dry-run default = synthetic; --submit para API real)
astrocitizen analyze plate-solve --fits-uri file://... --backend nova \
  --ra-hint 180 --dec-hint 10 --api-key KEY --submit

# Medir com WCS resultante
astrocitizen analyze astrometry --fits-uri <wcs_uri> --x 42 --y 32
```

## Limites

- `auto`: usa `solve-field` se no PATH; senao `synthetic` (requer hints).
- Nova upload multipart e minimo; polling com timeout.
- Sem index files / blind solve sem hints no backend synthetic.

## DoD

- [x] Port + 3 backends
- [x] Produto no BD + artefacto FITS
- [x] CLI + testes sem solver externo
- [x] Backlog AC-110 marcado
