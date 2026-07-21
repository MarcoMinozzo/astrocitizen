# Sprint — Esqueletos PO-B01 / C01–C03 (AC-083 / 085 / 086)

**Data:** 2026-07-21  
**Estado:** concluido

## Objetivo

Fechar o gap entre templates de catalogo e pipelines de analise minimos que alimentam Contribute (BeSS / MPC / TNS).

## Entregas

| Ticket | Template | Analise CLI | Export |
|--------|----------|-------------|--------|
| AC-083 | PO-B01 | `analyze spectrum` | `contribute bess --product` |
| AC-085 | PO-C01 / C02 | `analyze astrometry` (`--nonsidereal` em C02) | `contribute mpc --product` |
| AC-086 | PO-C03 | `analyze blink` | `contribute tns --product` |

Tambem registados em `P1_WORKFLOWS`: PO-A05, PO-B02, PO-D01 (metadados alinhados aos exports ja existentes).

## Limites do esqueleto

- Espectro: soma espacial + solucao linear de lambda (sem ISIS/extracao otimizada).
- Astrometria: WCS do header **ou** tan-plane com `--ra0/--dec0/--scale-arcsec` (sem plate-solve externo).
- Blink: diferenca de frames + pico residual (sem alinhamento avancado).

## DoD

- [x] Workflows em `programs/workflows.py`
- [x] Modulos `analysis/spectroscopy.py`, `astrometry.py`, `blink.py`
- [x] CLI analyze + contribute `--product`
- [x] Testes `tests/test_po_skeletons_b_c.py`
- [x] Backlog marcado
