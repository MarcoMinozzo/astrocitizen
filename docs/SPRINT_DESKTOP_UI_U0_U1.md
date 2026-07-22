# Sprint — Desktop UI U0/U1 (IA 6 areas)

**Data:** 2026-07-22  
**Estado:** concluido  
**Base:** [DESKTOP_UI_DESIGN.md](DESKTOP_UI_DESIGN.md)

## Entregas

1. **U0** `desktop/widgets.py`: `refill_site_combo` / `refill_program_combo`, `PathBrowseRow`, `ContextBar`, `TabHub`.
2. **U1** shell: nav **Noite · Observatorio · Analisar · Contribuir · Arquivo · Configurar**.
3. Hubs com tabs: Observatorio (Sessao/Importar/Observar/Timing), Configurar (4 CRUDs), Analisar (placeholder + Radio + Especialidades), Noite (Meteo + Planos).
4. Context bar global (site / programa / data / badge).
5. Theme: `brandBar` + `contextBar` no stylesheet (sem CSS inline).

## Seguinte

- **U2** Import hub unificado (canais IN-* num so tab Importar)
- Sync ContextBar → combos dos paineis (eliminar duplicacao)
- **U3** Arquivo rico + bridges Analisar

## DoD

- [x] ≤ 6 itens nav
- [x] Testes U0/U1
- [x] Funcionalidade ENTRADA preservada (paineis existentes em tabs)
