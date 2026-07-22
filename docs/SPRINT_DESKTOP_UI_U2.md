# Sprint — Desktop UI U2 (Import hub + ContextBar sync)

**Data:** 2026-07-22  
**Estado:** concluido  
**Base:** [DESKTOP_UI_DESIGN.md](DESKTOP_UI_DESIGN.md)

## Entregas

1. **Import hub** em Observatorio → Importar: tabs **FITS · Radio · Especialidades · Video/SER**.
2. Radio e Especialidades saem de Analisar (Analisar fica so bridges CLI: Fotometria / Espectro / Astrometria).
3. **ContextBar sync**: `set_shell_context` nos paineis Sessao, Import, Observar, Timing, Radio, Especialidades; mudanca na barra propaga Site/Programa.
4. Helper `select_combo_data` em `widgets.py`.

## Video / SER

Hint no hub: ocultacao → Timing; speckle → Especialidades.

## Seguinte

- **U3** Arquivo rico + bridges Analisar com output
- Ocultar combos locais Site/Programa quando ContextBar estiver activo (opcional)

## DoD

- [x] Importar unifica canais IN-* de ficheiro
- [x] Analisar sem entrada de dados
- [x] ContextBar sincroniza paineis
- [x] Testes
