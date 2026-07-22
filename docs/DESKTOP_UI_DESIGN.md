# Desktop UI — informacao architecture e design

**Status:** U0–U2 implementados · U3–U4 abertos  
**Data:** 2026-07-22  
**Codigo actual:** `src/astrocitizen/desktop/` · tema `theme.py` · widgets `widgets.py`  
**Fontes:** [WORKFLOWS.md](WORKFLOWS.md) §3–4, [ENTRADA_OBSERVACOES_POR_PO.md](ENTRADA_OBSERVACOES_POR_PO.md) §5–7, [SPRINT_UX_SHELL.md](SPRINT_UX_SHELL.md), [SPRINT_DESKTOP_UI_U0_U1.md](SPRINT_DESKTOP_UI_U0_U1.md)

---

## 1. Problema

A shell cresceu por sprint de **entrada de dados** (Import, Observar, Timing, Radio, Especialidades). Funcionalmente cobre ENTRADA §7, mas:

1. **Nav flat com 14 itens** — mistura operacao, CRUD e nichos P4.
2. **Diverge do mapa WORKFLOWS** (Início / Planejamento / Observatório / Análise / Contribuição / Diagnóstico).
3. **Diverge das 7 superficies ENTRADA** (agrupadas por canal, nao por ficheiro de sprint).
4. **Duplicacao** — Site/Programa combo e browse+path reimplementados em quase todos os paineis.
5. **Buraco na jornada** — Analisar existe no CLI, quase ausente na GUI.

O tema ops (navy + amber, IBM Plex, brand bar) e **bom suficiente** como base visual. O problema principal e **informacao architecture**, nao uma nova skin.

---

## 2. Inventario actual (pos-U1)

| Nav (6 areas) | Conteudo | Nota |
|---------------|----------|------|
| Noite | Meteo/radar + tab Planos | Hub |
| Observatorio | Sessao \| **Importar** (FITS/Radio/Espec./SER) \| Observar \| Timing | Hub |
| Analisar | Fotometria \| Espectro \| Astrometria (CLI bridges) | U3/U4 |
| Contribuir | `contribute.py` | Como antes |
| Arquivo | stub tabela obs | U3 |
| Configurar | Sites \| Equip \| Programas \| Alvos | Hub tabs |

Tokens: `COLORS` + `brandBar` / `contextBar` + visao noturna. ContextBar sincroniza Site/Programa nos paineis.

---

## 3. Alvo de produto (duas fontes, uma IA)

### WORKFLOWS — quatro modos

```
Configurar → Planejar → Executar → Analisar/Contribuir
```

### ENTRADA — sete superficies de entrada/analise

Sessao/Captura · Importador · Fotometria · Espectro · Astrometria/Blink · Timing · Log/Safety/Visual

**Regra de desenho:** top-level = **modo / area de trabalho**. Canais IN-* e PO-* = **tabs ou modos dentro** da area — nunca 1 item de nav por PO-*.

---

## 4. Proposta: 6 areas top-level

| Area | Conteudo | Substitui |
|------|----------|-----------|
| **Noite** | Meteo, radar, viabilidade, gerar/abrir plano | Noite + (Plano embutido) |
| **Observatorio** | Tabs: **Sessao** \| **Importar** \| **Observar** \| **Timing** | Sessao, Import, Observar, Timing |
| **Analisar** | Tabs: Fotometria \| Espectro \| Astrometria \| Radio \| Especialidades | Radio, Especialidades + bridges CLI |
| **Contribuir** | Redes + pendentes (como hoje) | Contribute |
| **Arquivo** | Obs + produtos + filtros/acções | Arquivo stub |
| **Configurar** | Tabs: Sites \| Equipamento \| Programas \| Alvos | 4 paginas CRUD |

**14 → 6.** Sessao volta a ficar junto de Import/Observar (fluxo de noite).

### Context bar (global)

Sob o brand bar, sempre visivel:

- Site activo  
- Programa activo (opcional)  
- Data da noite  
- Badge viabilidade (quando houver snapshot)

Paineis **consomem** este contexto; deixam de repetir combos Site/Programa excepto quando precisarem override local.

---

## 5. Principios

1. **Ops first** — Noite + Observatorio sao o hero; Configurar e nichos nao competem na nav primaria.
2. **Uma superficie, muitos canais** — Importar e hub IN-IMP/IN-RAD/IN-VID/P4, nao um ecran por formato.
3. **CLI = espelho** — cada tab tem comando; Analisar pode comecar a mostrar output de `analyze *`.
4. **Componentes partilhados antes de features** — `PathBrowseRow`, `ContextBar`, `PanelChrome` (titulo + hint + log).
5. **Preservar tema** — navy/amber por defeito; **visao noturna** (vermelho) para campo; unificar brand bar com `COLORS`.

### Visao noturna

Botao **Visao noturna** na brand bar (checkable). Aplica `NIGHT_VISION_COLORS` via `apply_theme(..., night_vision=True)`. Preferencia em `QSettings(AstroCitizen/desktop)`.


---

## 6. Roadmap (fases UX)

| Fase | Entrega | Domínio novo? |
|------|---------|---------------|
| **U0** | Doc + extrair widgets partilhados | ✅ `desktop/widgets.py` |
| **U1** | Nav 6 areas + Observatorio/Configurar/Analisar hubs | ✅ shell `app.py` |
| **U2** | Import hub (FITS/Radio/SER/Echelle/Speckle/Polar) | ✅ Observatorio→Importar + ContextBar sync |
| **U3** | Arquivo rico + shell Analisar (CLI bridge) | Minimo (tabs Analisar prontas) |
| **U4** | Viewer FITS / plots nas tabs Analisar | Sim (AC-062 GUI) |

## Aceite U1

- [x] Nav com ≤ 6 itens top-level  
- [x] Observatorio contem Sessao + Import + Observar + Timing  
- [x] Configurar agrupa os 4 CRUDs  
- [x] Context bar com site / programa / data  
- [x] Theme tokens brandBar + contextBar no stylesheet  
- [x] Testes `test_desktop_ui_u0_u1.py`  

## Aceite U2

- [x] Import hub com FITS / Radio / Especialidades / Video-SER  
- [x] Analisar so reducao (sem Radio/Espec. como entrada)  
- [x] ContextBar → `set_shell_context` nos paineis de observatorio  

## Historico

| Ver. | Data | Nota |
|------|------|------|
| 1.0 | 2026-07-22 | Estudo pos-ENTRADA; proposta 6 areas + roadmap U0–U4 |
| 1.1 | 2026-07-22 | U0+U1 implementados (widgets + nav 6 areas) |
| 1.2 | 2026-07-22 | U2 Import hub + ContextBar sync |
