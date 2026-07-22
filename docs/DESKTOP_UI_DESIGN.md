# Desktop UI — informacao architecture e design

**Status:** ✅ U0–U4 fechados (2026-07-22)  
**Data:** 2026-07-22  
**Codigo actual:** `src/astrocitizen/desktop/` · tema `theme.py` · widgets `widgets.py`  
**Fontes:** [WORKFLOWS.md](WORKFLOWS.md) §3–4, [ENTRADA_OBSERVACOES_POR_PO.md](ENTRADA_OBSERVACOES_POR_PO.md) §5–7, [SPRINT_UX_SHELL.md](SPRINT_UX_SHELL.md), [SPRINT_DESKTOP_UI_U0_U1.md](SPRINT_DESKTOP_UI_U0_U1.md), [SPRINT_DESKTOP_UI_U2.md](SPRINT_DESKTOP_UI_U2.md), [SPRINT_DESKTOP_UI_U3_U4.md](SPRINT_DESKTOP_UI_U3_U4.md)

---

## 1. Problema (resolvido na shell)

A shell cresceu por sprint de entrada; U0–U4 reorganizaram IA, hubs e Analisar/Arquivo.

---

## 2. Inventario actual (pos-U4)

| Nav (6 areas) | Conteudo | Nota |
|---------------|----------|------|
| Noite | Meteo/radar + tab Planos | Hub |
| Observatorio | Sessao \| Importar (FITS/Radio/Espec./SER) \| Observar \| Timing | Hub |
| Analisar | Fotometria \| Espectro \| Blink \| Viewer FITS | Bridges + AC-062 |
| Contribuir | Redes | |
| Arquivo | Observacoes + Produtos + filtros | U3 |
| Configurar | Sites \| Equip \| Programas \| Alvos | Hub |

Extras: ContextBar sync Site/Programa; Visao noturna (vermelho).

---

## 3–5. Alvo / principios

Mantidos: 4 modos WORKFLOWS, 7 superficies ENTRADA, ops first, CLI=espelho, tema navy/amber + NV.

---

## 6. Roadmap UX

| Fase | Entrega | Estado |
|------|---------|--------|
| **U0** | Widgets partilhados | ✅ |
| **U1** | Nav 6 areas + hubs | ✅ |
| **U2** | Import hub + ContextBar sync | ✅ |
| **U3** | Arquivo rico + Analisar bridges | ✅ |
| **U4** | Viewer FITS | ✅ |

## Melhorias futuras (fora deste epic UX)

- Ocultar combos locais quando ContextBar activo  
- Plots de curvas / espectro na GUI  
- Plate-solve externo na tab Astrom  
- Arquivo: abrir artefacto / export directo  

## Historico

| Ver. | Data | Nota |
|------|------|------|
| 1.0 | 2026-07-22 | Estudo pos-ENTRADA |
| 1.1 | 2026-07-22 | U0+U1 |
| 1.2 | 2026-07-22 | U2 |
| 1.3 | 2026-07-22 | U3+U4 — roadmap UX fechado |
