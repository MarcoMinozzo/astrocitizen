# Sprint — UX shell (tema + Noite async)

**Data:** 2026-07-21  
**Estado:** concluido  
**Base:** auditoria UX (theme ? Noite badges/async ? Contribute ja feito)

## Entregas

1. **Tema ops** (`desktop/theme.py`): navy + amber, tipografia IBM Plex/Segoe, stylesheet global.
2. **Shell** (`app.py`): brand bar AstroCitizen, nav com estado activo, status bar, empty states nas tabelas.
3. **Noite** (`night.py`): badge VIABLE/INVIABLE; `Atualizar noite` em QThread (UI nao bloqueia); botao plano como secondary.

## Fora de ambito (seguinte)

- Wizard Sessao (start ? capture ? FITS)
- Formularios CRUD inline nas listas
- Loading spinner dedicado / cancelamento de fetch

## DoD

- [x] Helpers testaveis sem display
- [x] Sem roxo / cream AI defaults
- [x] Contribute permanece na nav
- [x] Backlog AC-071/072/073/073a anotado
