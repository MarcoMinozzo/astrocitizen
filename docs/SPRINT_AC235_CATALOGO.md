# Sprint AC-235 / AC-236 — Catálogo próprio + fotometria SIMBAD

**Status:** feito · **Data:** 2026-07-24  
**Épico:** [EPICO_E22_HUB_CIENTIFICO.md](EPICO_E22_HUB_CIENTIFICO.md) · UX: [UX_E22_INTEROPERABILIDADE.md](UX_E22_INTEROPERABILIDADE.md)

## Objectivo

1. **Buffer próprio** (`catalog_objects`): cada busca de objecto actualiza o nosso catálogo (Desktop + sync SaaS).
2. **Menu Catálogo** na shell: ficha por secções (identidade, posição, fotometria, …).
3. **Fotometria correcta por tipo** (AC-236): sem confundir mag de estrela Gaia com o objecto.

## Entregue

| Peça | Notas |
|------|--------|
| Schema v11 `catalog_objects` | Archive CRUD + `catalog dossier` / `list` |
| `CatalogDossierService` | Multi-API → secções → upsert (+ enqueue sync) |
| GUI nav **Catalogo** | Busca síncrona fiável; formulário por domínio |
| Política objectos extensos | GlC/Galaxy/Neb…: **sem** cone Gaia/VizieR como `mag_max` |
| Harris VII/202 | Globulares → `vmag` / Vt (ex. M56 ≈ 8.27) |
| SIMBAD TAP `allfluxes` | B/V/R/… (ex. NGC1200: B=13.0, R=11.42; sem V no SIMBAD) |
| Sync `entity=catalog_object` | Fila Desktop → SaaS master |

## Política de fotometria (normativa)

| Tipo | Fonte de mag de referência | Não fazer |
|------|----------------------------|-----------|
| Variável (VSX) | `mag_max` / `mag_min` VSX | Sobrescrever com Gaia G |
| Globular (GlC) | Harris `Vt` → `vmag` | Cone Gaia como mag do enxame |
| Galáxia / Neb / etc. | SIMBAD TAP B/V/R (o que existir) | Promover G de estrela no campo |
| Estrela pontual | VSX e/ou SIMBAD; Gaia G só como `gmag` auxiliar | Usar `gmag` como mag_max do alvo se houver V/VSX |

`band_notes` deve explicar a banda (ex. «SIMBAD B=…, R=… (ref R, sem V)»).

## CLI útil

```bash
astrocitizen catalog dossier --name "NGC1200"
astrocitizen catalog dossier --name "M56"
astrocitizen catalog list
astrocitizen catalog resolve --name "SS Cyg"
```

## Estabilidade GUI (notas operacionais)

- **Qt WebEngine** (Campanhas AAVSO): opt-in `ASTROCITIZEN_WEBENGINE=1` (+ extra `gui-web`). Default = browser do SO (evita segfault Chromium).
- **Noite**: sem auto-refresh de meteo no arranque/sync do ContextBar; usar «Actualizar noite».
- **Catálogo**: lookup na thread UI (rede 2–5 s) — evita QThread+SQLite+QMessageBox cross-thread.

## Lacunas conhecidas (próximos)

- Catálogos dedicados de galáxias (PGC/LEDA, 2MASS XSC) quando SIMBAD não tem V.
- Espectroscopia na ficha ainda reservada (Fase 2 ARAS/BeSS).
- SaaS master ainda SQLite scaffold (Postgres a seguir).

## Commits de referência

- `51d6a3e` — buffer + ficha + nav (AC-235)
- `536acf3` — fotometria extensos / Harris / UI thread
- `b567a81` — SIMBAD TAP + estabilização GUI (AC-236)
