---
chunk_id: docs-analise-espectral-002
source_id: docs-analise-espectral
path: docs/ANALISE_ESPECTRAL_ASSISTIDA.md
title: 2.2 Deteccao de linhas
trust_tier: T3
lang: pt
topics: ["spectrum", "analysis"]
po_id: PO-B01
network: null
pipeline_stage: help
token_estimate: 360
chunk_hash: "sha256:b2af27882d5e2a9fc1fbeef54b31d7f50dc213a71d940fb3c82f481df888d2af"
corpus_version: 0.1.0-kb1
---

## 2.2 Deteccao de linhas

Catalogo fixo (`LINE_CATALOG`): H-delta…H-alpha, He I 5876, Na D, Si II 6355, O2 A ~7605 A, Ca II 8542.

Para cada linha:

1. Janela de ±`half_width_A` (default 40 A).
2. Continuo **local** = mediana dos terços externos da janela.
3. Ruido local (MAD × 1.4826); fallback para ruido global.
4. Se pico − continuo ≥ `snr_min` → emissao; senao se continuo − vale ≥ `snr_min` → absorcao.
5. Ordenacao por forca (SNR).

## 2.3 Pista de classe (`classify_hint`)

Regras simples, confianca tipicamente `low`/`medium`:

- Balmer em emissao e sem Si II forte em absorcao → `H-rich (SN II-like / Be / emission-line)`.
- Si II 6355 em absorcao forte → candidato Ia-like (sempre a confirmar com templates).
- O2 A detetado → nota telúrica obrigatoria.

## 2.4 Multi-epoca

Cada epoca: `date_obs`, `blue_red_ratio`, `n_features`.  
Entre epocas ordenadas por data: se o ratio mudar >15%, anota queda/subida relativa do continuo azul.

## 2.5 Saida

1. Ficheiro texto `#TYPE=ASTROCITIZEN_SPECTRUM_REPORT` (artefacto no store).
2. `AnalysisProduct` com `product_type=spectrum_report` no Archive (SQLite).

Campos uteis em `summary`: `class_hint`, `confidence`, `top_line`, `n_features`, `blue_red_ratio`, `n_epochs`.

---

## 3. CLI

```bash
astrocitizen analyze spectrum-report \
  --fits-uri file:///caminho/espectro_1d.fits \
  --out /tmp/report.txt

astrocitizen analyze spectrum-report \
  --product <uuid-spectrum_1d> \
  --extra-products <uuid2>,<uuid3>
```

Workflows: passo `interpret_spectrum` em PO-B01, PO-B02, PO-B03.

---

## 4. O que ainda nao faz (backlog)

| Item | Notas |
|------|-------|
| AC-102 completo | EW, ajuste gaussiano, redshift preciso |
| AC-107 | Camada **LLM** opcional (narrativa) — ver abaixo |
| GUI Analisar | Painel para abrir o relatorio |
| Templates SN | Matching espectral formal (fora do AC-106) |

---
