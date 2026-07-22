# Analise espectral assistida (AC-106)

**Estado:** entregue (commit `1224256`, 2026-07-22)  
**Backlog:** AC-106 · workflows PO-B01 / PO-B02 / PO-B03  
**Sprint:** [SPRINT_SPECTRUM_REPORT.md](SPRINT_SPECTRUM_REPORT.md)  
**Codigo:** `src/astrocitizen/analysis/spectrum_report.py`

---

## 1. O que e

Funcao da plataforma que, a partir de um espectro 1D (FITS), produz um **relatorio estruturado e reprodutivel**:

- linhas candidatas (emissao / absorcao) perto de um catalogo fixo;
- nota de banda telúrica O2 (atmosfera, nao astrofisica);
- pista grosseira de classe (ex.: H-rich vs Si II Ia-like);
- razao de continuo azul/vermelho;
- comparacao **multi-epoca** (evolucao relativa do continuo).

Inspiracao: analise cidada estilo ARAS / series SN (ex.: SN2026sqf).

**Nao e classificacao oficial SN nem substituto de templates / revisao humana.**

---

## 2. Como funciona (sem LLM)

A pipeline e **deterministica** (NumPy + Astropy). Nao ha modelo generativo no caminho critico.

```text
FITS 1D (lambda, flux)
        |
        v
 load_spectrum_arrays   (CRVAL/CDELT/CUNIT -> Angstrom)
        |
        v
 detect_line_features   (janela + continuo local + SNR)
        |
        +--> classify_hint          (regras sobre Balmer / Si II / O2)
        +--> continuum_blue_red     (4000-5000 vs 6500-7500 A)
        |
        (+ epocas extra via produtos spectrum_1d)
        |
        v
 compare_epochs         (delta relativo do blue/red ratio)
        |
        v
 format_spectrum_report -> .txt + AnalysisProduct spectrum_report
```

### 2.1 Entrada

| Fonte | Como |
|-------|------|
| FITS 1D | CLI `--fits-uri` ou URI no store |
| Produto `spectrum_1d` | CLI `--product <uuid>` (usa `spectrum_uri` / `fits_uri`) |
| Extra epocas | `--extra-products uuid1,uuid2` |

Cabecalhos uteis: `OBJECT`, `DATE-OBS`, `INSTRUME`, `CRVAL1`/`CDELT1`/`CRPIX1`, `CUNIT1` (nm convertido para Angstrom).

### 2.2 Deteccao de linhas

Catalogo fixo (`LINE_CATALOG`): H-delta…H-alpha, He I 5876, Na D, Si II 6355, O2 A ~7605 A, Ca II 8542.

Para cada linha:

1. Janela de ±`half_width_A` (default 40 A).
2. Continuo **local** = mediana dos terços externos da janela.
3. Ruido local (MAD × 1.4826); fallback para ruido global.
4. Se pico − continuo ≥ `snr_min` → emissao; senao se continuo − vale ≥ `snr_min` → absorcao.
5. Ordenacao por forca (SNR).

### 2.3 Pista de classe (`classify_hint`)

Regras simples, confianca tipicamente `low`/`medium`:

- Balmer em emissao e sem Si II forte em absorcao → `H-rich (SN II-like / Be / emission-line)`.
- Si II 6355 em absorcao forte → candidato Ia-like (sempre a confirmar com templates).
- O2 A detetado → nota telúrica obrigatoria.

### 2.4 Multi-epoca

Cada epoca: `date_obs`, `blue_red_ratio`, `n_features`.  
Entre epocas ordenadas por data: se o ratio mudar >15%, anota queda/subida relativa do continuo azul.

### 2.5 Saida

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

## 5. LLM (planejado) — nao substitui medidas

Principio: **medidas fisicas primeiro; linguagem depois**.

| ID | Ideia |
|----|-------|
| AC-107 | Narrativa LLM a partir do `spectrum_report` (e so dele + contexto citado) |
| AC-108 | Modo offline / opt-in; sem LLM o fluxo AC-106 continua a funcionar |
| AC-109 | Guardrails: nao inventar linhas; citar FEATURES do relatorio; marcar incerteza |

A camada LLM **nao** deve recalcular fluxos nem classificar SN sozinha. Idealmente usa **RAG (E19)** para citar docs ARAS/BeSS/atlas internos.

---

## 6. Relacao com RAG (E19)

A base de conhecimento interna (E19) alimenta respostas contextualizadas, por exemplo:

- “o que significa O2 A no meu relatorio?” → chunk atlas / guia espectral;
- “proximo passo PO-B03 / ARAS” → docs de workflow e redes.

Ver [EPICO_E19_BASE_CONHECIMENTO_RAG.md](EPICO_E19_BASE_CONHECIMENTO_RAG.md).
