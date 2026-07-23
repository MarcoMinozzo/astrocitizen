---
chunk_id: atlas-reporte-004
source_id: atlas-reporte
path: docs/atlas/ATLAS_REPORTE_OBSERVACOES.md
title: Fontes oficiais
trust_tier: T3
lang: pt
topics: ["networks", "export"]
po_id: null
network: bess
pipeline_stage: help
token_estimate: 682
chunk_hash: "sha256:f569605dc898d51c2af8c661f55fc9872862f09cb9678b8bfa1f83d068247ccd"
corpus_version: 0.1.0-kb1
---

## Fontes oficiais

- https://www.wis-tns.org/  
- https://www.wis-tns.org/content/tns-getting-started  
- https://www.wis-tns.org/sites/default/files/api/tns2_manuals/TNS2.0_bulk_reports_manual.pdf  
- Dados estendidos de LC/espectros: WISeREP (https://www.wiserep.org) — TNS **não** substitui repositório de curvas longas

## Nota

Variáveis galácticas / novas clássicas **não** devem ir ao TNS (orientação oficial TNS).

---

## 3.7 BeSS (+ ecossistema ARAS)

| | |
|--|--|
| **PO-*** | B02, B03; B01 quando alvo Be |
| **Canal** | Upload no site BeSS (primeiro espectro validado por admins → login) |
| **Formato** | **FITS 1D** (HDU único), keywords BeSS / `BSS_*` |
| **Arquivos** | `.fits` ou archive `.zip` / `.tar.gz` ≤ 15 MB |
| **Nível** | A |

## Requisitos científicos (especificação BeSS)

- Alvo Be do catálogo BeSS (ou contato com admins)  
- Espectro **pré-processado e calibrado em λ** (bias/dark/flat, geometria, céu, extração, calibração linear)  
- OBSERVER presente  
- Normalização / telluric / Vhelio: desaconselhados; se feitos, keywords obrigatórias

## Keywords (resumo)

- Identificação: `OBJNAME` **ou** `RA`+`DEC` (+ equinox/FK5)  
- Tempo: 2 entre `DATE-OBS`, `DATE-END`, `EXPTIME`  
- Site: `BSS_SITE` **ou** lat/long/elev **ou** satélite  
- Instrumento: `BSS_INST` **ou** `TELESCOP`+`DETNAM`+`INSTRUME`  
- WCS espectral: `CRVAL1`, `CDELT1`, `CRPIX1`, `CTYPE1`, `CUNIT1`, …  
- Resolução indicativa: `BSS_ESRP` / correlatos

## Fontes oficiais

- Spec BeSS (PDF): http://basebe.obspm.fr/basebe/Spec_spectres_BeSS_en.pdf  
- Portal BeSS: http://basebe.obspm.fr/  
- Paper BeSS: Neiner et al. (AJ)  
- ARAS: campanhas/alertas e convenções de nome de arquivo no fórum spectro-aras (complementar a BeSS)

## Dados no BD AstroCitizen

FITS 1D URI · header keywords · observer · site · instrument · DATE-OBS · resolution · BeSS upload status · raw frames retention note (obrigação BeSS: manter brutos)  

---

## 3.8 IOTA — Ocultações

| | |
|--|--|
| **PO-*** | D01–D04 |
| **Canal** | **Regional** (não um único formulário global) |
| **Nível** | B |

## América do Norte / AU-NZ (exemplo)

- Formulário Excel oficial (Asteroid Report Forms, versões atualizadas)  
- Upload via **IOTA Hub** (iota-hub.com) com arquivos de suporte  
- Nomeação típica: `YYYYMMDD_AstNo_AstName_ObserverLastName_pos/neg.xls`  
- Anexos: CSV PyMovie/LiMovie/Tangra · log PYOTE/ROTE/Occular/AOTA · gráfico de curva de luz

## Europa (IOTA-ES)

- **SODIS** + formulário texto tipo Occult/OW (`IOTA-ES_report_*.txt`)  
- Preencher via Occult Watcher Report add-in quando possível

## Ásia (IOTA/EA)

- E-mail regional (`asteroid-report@…`, `lunar-report@…`) + docs PDF oficiais

## Lunar

- Canal distinto: http://lunar-occultations.com/iota/lunarreport.htm

## Fontes oficiais

- https://occultations.org/observing/reporting-observations/  
- https://www.asteroidoccultation.com/observations/Forms/AsteroidReportForms.html  
- https://asteroidoccultations.com/observations/  
- SODIS manual (IOTA-ES)

## Dados no BD AstroCitizen

Event ID · star · asteroid · site lat/lon/elev · timesource (GPS/VTI…) · D/R times (+σ) · pos/neg · instrument/camera · weather · analysis software · report package URI · hub region  

---

## 3.9 WDS — Washington Double Star Catalog

| | |
|--|--|
| **PO-*** | G01 |
| **Canal** | Contribuição ao USNO / maintainer WDS (medidas publicáveis) |
| **Formato** | Catálogo WDS tem layout colunar fixo; novas medidas seguem práticas USNO (contato/instruções vigentes) |
| **Nível** | B |

## Dados típicos de uma medida

Época · ângulo de posição (°) · separação (″) · magnitudes · identificação do par (discoverer designation / WDS) · método · observatório

## Fontes

- https://www.astro.gsu.edu/wds/ (USNO WDS)  
- ReadMe CDS B/wds  

---
