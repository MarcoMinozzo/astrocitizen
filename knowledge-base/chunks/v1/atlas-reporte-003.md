---
chunk_id: atlas-reporte-003
source_id: atlas-reporte
path: docs/atlas/ATLAS_REPORTE_OBSERVACOES.md
title: 3.3 µFUN — Microlensing
trust_tier: T3
lang: pt
topics: ["networks", "export"]
po_id: null
network: aavso
pipeline_stage: help
token_estimate: 697
chunk_hash: "sha256:ee4dfd3d962448e1392bb6a9b530415e1c63ec75b31777a3413d160b9b8b65a8"
corpus_version: 0.1.0-kb1
---

## 3.3 µFUN — Microlensing

| | |
|--|--|
| **PO-*** | A06 |
| **Canal** | Coordenação por alertas µFUN / PI da campanha (historicamente e-mail + fotometria densa) |
| **Formato** | Não há um único “file format” público estável como AAVSO; tipicamente séries fotométricas + metadados de site/instrumento conforme instruções do alerta |
| **Nível** | B |

## Política AstroCitizen

- Persistir curva completa no BD no esquema fotométrico interno  
- Export “genérico” CSV/FITS table + pacote de metadados  
- Campos mínimos: target (event ID), HJD/BJD, mag/flux, err, filter, site, telescope, observer

## Fonte / contexto

- Literatura do acervo: pasta `microfun/`  
- Acompanhar site/alertas µFUN vigentes na época da implementação  

---

## 3.4 MPC — Minor Planet Center (astrometria)

| | |
|--|--|
| **PO-*** | C01, C02, C04, C05; apoio A09/A10 se houver astrometria |
| **Canal** | Formulários web ADES ou cURL (`submit_xml` / `submit_psv`) — **não** e-mail para ADES |
| **Formato oficial** | **ADES** (Astrometry Data Exchange Standard): **XML** (preferido) ou **PSV** (pipe-separated). MPC1992 80-colunas obsoleto para códigos novos |
| **Validação** | Schema `submit.xsd` |
| **Nível** | A |

## Pré-requisitos

- **Observatory code** MPC  
- Conformidade com *Guide to Minor Body Astrometry* (além do formato)

## Submissão (exemplos oficiais)

```bash
# XML
curl -L https://minorplanetcenter.net/submit_xml \
  -F "ack=message" -F "ac2=email@example.com" \
  -F "obj_type=NEO" -F "source=<file.xml"

# PSV
curl -L https://minorplanetcenter.net/submit_psv \
  -F "ack=message" -F "ac2=email@example.com" \
  -F "obj_type=NEO" -F "source=<file.psv"
```

`obj_type`: NEO, comet, TNO, NEOCP, etc. (conforme formulário).

## Dados típicos ADES (conceito)

Observatory · object designation · epoch (UTC) · RA/Dec (+ incertezas) · mag (+ banda) · catalogo de referência · modo de observação · observador/programa

## Fontes oficiais

- https://minorplanetcenter.net/mpcops/documentation/ades/  
- https://data.minorplanetcenter.net/iau/info/Astrometry.html  
- https://docs.minorplanetcenter.net/mpc-ops-docs/observations/command-line-submissions/  
- https://minorplanetcenter.net/submit_xml · https://minorplanetcenter.net/submit_psv  
- ADES GitHub (especificação IAU)

## Dados no BD AstroCitizen

MPC code · designation · epoch · RA/Dec/σ · mag/band · ADES XML/PSV artifact URI · submission ack/CurlID · status  

---

## 3.5 COBS / ICQ — Cometas (fotometria / visual)

| | |
|--|--|
| **PO-*** | A10 (fotometria); imaging E06 pode coexistir localmente |
| **Canal** | COBS web form (armazena em formato ICQ) e/ou contribuição ICQ |
| **Formato** | **ICQ 80-column** (+ extensão CCD após col. 80 desde 2002) |
| **Nível** | A |

## Dados típicos ICQ

UT date (0.01 d) · magnitude total · método de mag · fonte das comps · instrumento (abertura, tipo, f/, exposição/mag) · diafragma, DC, cauda, PA, etc. · campos CCD extras

## Fontes oficiais

- https://www.cobs.si/ · https://www.cobs.si/help/icq_format/  
- http://www.icq.eps.harvard.edu/ICQFormat.html  

---

## 3.6 TNS — Transient Name Server (supernovas / AT)

| | |
|--|--|
| **PO-*** | C03 |
| **Canal** | Formulários web interativos **ou** Bulk API JSON (bots) |
| **Ambiente de teste** | https://sandbox.wis-tns.org (obrigatório para desenvolver API) |
| **Nível** | A |

## Tipos de reporte

1. **AT-rep** (discovery): coordenadas, grupo, fonte de dados, fotometria de descoberta (**obrigatória**), última non-detection, arquivos relacionados (finding chart…)  
2. **Class-rep** (classification): espectro de suporte; prefixo AT→SN quando aplicável

## Formato API

JSON conforme manuais TNS 2.0 (IDs de grupo, instrumento, filtro via tabelas AUX).
