# Sprint — Desktop UI U5 (plots + Arquivo detalhe)

**Data:** 2026-07-22  
**Estado:** concluido  
**Base:** [DESKTOP_UI_DESIGN.md](DESKTOP_UI_DESIGN.md)

## Entregas

1. **`series.py`**: extrai (x, y) de `measurement_points`; formata detalhe de produto.
2. **`plot_widget.py`**: plot XY com QPainter (sem matplotlib; respeita tema / visao noturna).
3. **Analisar → Curvas**: carrega product UUID e plota pontos; UUID preenchido apos fotometria/espectro.
4. **Arquivo → Produtos**: selecao mostra detalhe + plot; Copiar UUID; Hint export (CLI contribute).

## DoD

- [x] Plot de curvas/espectro na GUI a partir do arquivo
- [x] Detalhe de produto + hint de export
- [x] Testes sem display (`test_desktop_ui_u5.py`)
