---
chunk_id: docs-entrada-005
source_id: docs-entrada
path: docs/ENTRADA_OBSERVACOES_POR_PO.md
title: E — Sistema Solar imaging
trust_tier: T3
lang: pt
topics: ["entrada", "channels"]
po_id: null
network: solar
pipeline_stage: help
token_estimate: 348
chunk_hash: "sha256:39eb27a013b653bd5a6d7bdd25a7d3cef751b9f0a11e1699451c93f9583a1d5d"
corpus_version: 0.1.0-kb1
---

## E — Sistema Solar imaging

| PO | Como o utilizador fornece | Canais | Payload mínimo | Produto | Estado |
|----|---------------------------|--------|----------------|---------|--------|
| **E01** Lua | SER/AVI/FITS + stack | IN-VID, IN-IMP | frames | stacked image | desenho |
| **E02** Planetas | Lucky imaging (SER) | IN-VID | SER | stacked | desenho |
| **E03** Sol WL | **Checklist safety** + FITS/imagem + contagem (auto/manual) | IN-LOG + IN-IMP | safety + image | `solar_sunspots` | parcial |
| **E04** Sol Hα | Safety + filtro Hα + imagem | IN-LOG + IN-IMP | safety + image | solar activity | desenho |
| **E05** Eclipses | Timing contacts + imaging | IN-LOG + IN-IMP | times + images | timing+image | desenho |
| **E06** Cometas img | Tracking + frames | IN-CAP, IN-IMP | FITS | image pack | desenho |

## F — Deep-sky / visual

| PO | Como o utilizador fornece | Canais | Payload mínimo | Produto | Estado |
|----|---------------------------|--------|----------------|---------|--------|
| **F01** Deep-sky | LRGB/Ha frames + calib | IN-CAP, IN-IMP | FITS set | stacked LRGB | desenho |
| **F02** Messier | Imaging **ou** log visual do objecto | IN-IMP **ou** IN-LOG | image ou log | archive / log | desenho |
| **F03** Visual | **Só formulário** (sem CCD): objecto, condições, descrição | IN-LOG | log JSON/texto | visual_log | ✅ Observar + `observe log-visual` |
| **F04** Asterismos | Planner + log de reconhecimento | IN-LOG | checklist céu | log | desenho |
