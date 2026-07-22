# Sprint — Programa activo (guia GUI)

**Data:** 2026-07-22  
**Estado:** concluido  
**Base:** [DESKTOP_UI_DESIGN.md](DESKTOP_UI_DESIGN.md), [WORKFLOWS.md](WORKFLOWS.md)

## Entregas

1. **`programs/guide.py`**: mapeamento passos PO-* → areas/tabs; normalizacao de redes.
2. **`desktop/program_active_panel.py`**: tab **Observatorio → Programa**
   - resumo do programa da ContextBar
   - alvos ligados + ligar alvo (primary/comp/check)
   - passos do workflow com navegacao
   - atalho **Abrir Contribuir** (filtro + tab da rede)
   - produtos recentes com `program_id`
3. **Contribuir** `focus_network`; **Analisar** `focus_tab`; shell `_navigate_to`.

## Uso

1. Configurar → Programas: criar a partir de template PO-* e activar  
2. ContextBar: seleccionar o programa  
3. Observatorio → Programa: ligar alvos, seguir passos, export  

## Limite

Continua a ser campanha **local** (etiqueta `program_id`), nao enrollment em rede remota.
