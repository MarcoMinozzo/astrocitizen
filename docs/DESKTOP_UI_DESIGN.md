# Desktop UI — informacao architecture e design

**Status:** ✅ U0–U5 (2026-07-22)  
**Data:** 2026-07-22  
**Codigo actual:** `src/astrocitizen/desktop/` · tema `theme.py` · widgets `widgets.py`  
**Fontes:** [WORKFLOWS.md](WORKFLOWS.md) §3–4, [ENTRADA_OBSERVACOES_POR_PO.md](ENTRADA_OBSERVACOES_POR_PO.md) §5–7, [SPRINT_UX_SHELL.md](SPRINT_UX_SHELL.md), [SPRINT_DESKTOP_UI_U0_U1.md](SPRINT_DESKTOP_UI_U0_U1.md), [SPRINT_DESKTOP_UI_U2.md](SPRINT_DESKTOP_UI_U2.md), [SPRINT_DESKTOP_UI_U3_U4.md](SPRINT_DESKTOP_UI_U3_U4.md), [SPRINT_DESKTOP_UI_U5.md](SPRINT_DESKTOP_UI_U5.md)

---

## 1. Problema (resolvido na shell)

A shell cresceu por sprint de entrada; U0–U4 reorganizaram IA, hubs e Analisar/Arquivo.

---

## 2. Inventario actual (pos-U5)

| Nav (6 areas) | Conteudo | Nota |
|---------------|----------|------|
| Noite | Meteo/radar + **carta do plano L0** (AC-079) + tab Planos | Hub |
| Observatorio | Programa activo \| Sessao \| Importar \| Observar \| Timing | Guia PO-* |
| Analisar | Fotometria \| Espectro \| Blink/Astrom (+ plate-solve + medida) \| Viewer \| Curvas | Bridges AC-110/111 GUI |
| Contribuir | Redes | |
| Arquivo | Observacoes + Produtos + detalhe/plot + abrir/export | U3+U5+abrir |
| Configurar | Sites \| Equip \| Programas \| Alvos \| Preferencias \| Ajuda | + idioma RN-120 |

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
| **U5** | Plots + Arquivo detalhe/export hint | ✅ |

## Melhorias futuras (fora deste epic UX)

- Ocultar combos locais quando ContextBar activo  
- Enrollment multi-observador / membership de programas partilhados  
- Contribuir: UI Revisar campos atlas — redes principais ✅ (R2/R3/WDS/COBS) 

## Historico

| Ver. | Data | Nota |
|------|------|------|
| 1.0 | 2026-07-22 | Estudo pos-ENTRADA |
| 1.1 | 2026-07-22 | U0+U1 |
| 1.2 | 2026-07-22 | U2 |
| 1.3 | 2026-07-22 | U3+U4 — roadmap UX fechado |
| 1.4 | 2026-07-22 | U5 plots + Arquivo detalhe |
| 1.5 | 2026-07-22 | Plate-solve GUI (AC-110 bridge) |
| 1.6 | 2026-07-22 | Painel Programa activo (guia + Contribuir) |
| 1.7 | 2026-07-22 | RN-120/121 i18n pt/es/en + Ajuda in-app |
| 1.8 | 2026-07-22 | Medida astrometria GUI (x,y → RA/Dec) |
| 1.9 | 2026-07-22 | Arquivo: abrir artefacto + export directo |
| 2.0 | 2026-07-23 | Noite: carta do plano L0 (AC-079; nao planetario) |
