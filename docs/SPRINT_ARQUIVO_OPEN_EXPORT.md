# Sprint — Arquivo abrir / export directo

**Data:** 2026-07-22  
**Estado:** concluido  
**Base:** [DESKTOP_UI_DESIGN.md](DESKTOP_UI_DESIGN.md), [SPRINT_DESKTOP_UI_U5.md](SPRINT_DESKTOP_UI_U5.md)

## Entregas

1. Helpers Qt-free em `desktop/series.py`: `primary_artifact_refs`,
   `resolve_openable_path`, `export_networks_for_type`, `cli_export_hint`.
2. **Arquivo → Produtos**:
   - **Abrir artefacto** via `QDesktopServices` (WCS/spectrum/fits/...).
   - **Exportar** menu: AAVSO / ExoClock / BeSS / solar directo;
     MPC/TNS saltam para Contribuir com UUID.
   - **Ver CLI** mantido como fallback.
3. `artifacts_root` + callback `on_contribute` ligados em `app.py`.
4. `ContributeDashboard.focus_network(..., product_id=)` preenche UUID.

## DoD

- [x] Abrir artefacto no OS a partir do produto
- [x] Export directo (AAVSO, ExoClock, BeSS, solar) sem so hint
- [x] Testes helpers (`test_desktop_ui_u5.py`)
- [x] Roadmap DESKTOP_UI actualizado
