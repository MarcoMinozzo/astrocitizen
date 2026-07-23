---
chunk_id: docs-analise-espectral-001
source_id: docs-analise-espectral
path: docs/ANALISE_ESPECTRAL_ASSISTIDA.md
title: Introduction
trust_tier: T3
lang: pt
topics: ["spectrum", "analysis"]
po_id: PO-B01
network: null
pipeline_stage: help
token_estimate: 326
chunk_hash: "sha256:b337011f6b4fb26a55a5433a93ea4162752d00546d14e787d62c81aa0fc46b24"
corpus_version: 0.1.0-kb1
---

## Introduction

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

## 2.1 Entrada

| Fonte | Como |
|-------|------|
| FITS 1D | CLI `--fits-uri` ou URI no store |
| Produto `spectrum_1d` | CLI `--product <uuid>` (usa `spectrum_uri` / `fits_uri`) |
| Extra epocas | `--extra-products uuid1,uuid2` |

Cabecalhos uteis: `OBJECT`, `DATE-OBS`, `INSTRUME`, `CRVAL1`/`CDELT1`/`CRPIX1`, `CUNIT1` (nm convertido para Angstrom).
