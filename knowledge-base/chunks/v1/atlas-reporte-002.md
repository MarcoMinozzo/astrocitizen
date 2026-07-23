---
chunk_id: atlas-reporte-002
source_id: atlas-reporte
path: docs/atlas/ATLAS_REPORTE_OBSERVACOES.md
title: 2. Mapa rápido Rede → Programas PO-*
trust_tier: T3
lang: pt
topics: ["networks", "export"]
po_id: null
network: aavso
pipeline_stage: help
token_estimate: 684
chunk_hash: "sha256:c25201e2f07c2a47fe11a7c1ece5586f4f18ec362243d645a8dd05d3b2250195"
corpus_version: 0.1.0-kb1
---

## 2. Mapa rápido Rede → Programas PO-*

| Rede | PO-* principais | Nível |
|------|-----------------|-------|
| **AAVSO** (AID / WebObs) | A01–A03, A05 (também Exoplanet DB), F03 visual | A |
| **ExoClock** | A05 | A |
| **µFUN** | A06 | B |
| **MPC** (ADES) | C01, C02, C04, C05, A09/A10 (astrometria) | A |
| **COBS / ICQ** | A10 (fotometria de cometas) | A |
| **TNS** (IAU) | C03 | A |
| **BeSS** (+ ARAS) | B02, B03 (e B01 quando Be) | A |
| **IOTA** (hubs regionais) | D01–D04 | B |
| **WDS / USNO** | G01 | B |
| **Redes solares** | E03, E04, B06, I01 | B–C |
| **Arquivo local AstroCitizen** | A04, A07, A08, B04–B08, E01–E02, E05–E06, F*, H*, I*, J*, K* | C–D |

---

## 3. Fichas por rede oficial

---

## 3.1 AAVSO — Variable Star Observations

| | |
|--|--|
| **PO-*** | A01, A02, A03; visual F03; trânsitos também via AAVSO Exoplanet (ver 3.2) |
| **Canal** | WebObs / Submit Photometric Observations (WebObs 2.0 em rollout) |
| **Formatos oficiais** | (1) **AAVSO Extended File Format** — CCD/DSLR/PEP/CMOS; (2) **AAVSO Visual File Format** — visual/fotográfico |
| **Extensões** | `.txt`, `.csv`, `.tsv` |
| **Nível** | A |

## Cabeçalho Extended (obrigatório)

```
#TYPE=Extended
#OBSCODE=<código AAVSO do observador>
#SOFTWARE=<nome e versão>
#DELIM=,   (ou tab / comma / ; etc.)
#DATE=JD   (ou HJD / EXCEL)
#OBSTYPE=CCD  (CCD|DSLR|PEP; CMOS reportar como CCD)
```

## Campos de cada linha (Extended)

`STARID, DATE, MAGNITUDE, MAGERR, FILTER, TRANS, MTYPE, CNAME, CMAG, KNAME, KMAG, AIRMASS, GROUP, CHART, NOTES`

- Opcionais ausentes → `na`  
- `MAGNITUDE`: ponto decimal obrigatório; `<` para fainter-than  
- `FILTER`: V, B, R, I, TG/TB/TR, CV/CR, Sloan, etc. (lista oficial AAVSO)  
- `TRANS`: YES/NO · `MTYPE`: STD (recomendado) ou DIF  
- `CHART`: Sequence ID da tabela VSP

## Pré-requisitos de conta

- Observer code AAVSO (`OBSCODE`)  
- Sequências/cartas VSP quando aplicável

## Fontes oficiais

- https://www.aavso.org/aavso-file-format-specifications  
- https://www.aavso.org/aavso-extended-file-format  
- https://www.aavso.org/aavso-visual-file-format  
- https://www.aavso.org/webobs/

## Dados que AstroCitizen deve persistir (BD)

Observer code · STARID/AUID · JD/HJD midpoint · mag · magerr · filter · transform flag · comp/check · airmass · chart/sequence · software · raw observation_ids  

---

## 3.2 ExoClock (+ ponte AAVSO Exoplanet)

| | |
|--|--|
| **PO-*** | A05 |
| **Canal** | Conta ExoClock → registrar telescópios → upload de curva de luz |
| **Formato** | Arquivo de fotometria reduzida (não FITS bruto): HOPS `…for ExoClock.txt` ou subset AIJ (`BJD_TDB`, flux normalizado, erro, airmass) |
| **Nível** | A |

## Fluxo oficial (resumo)

1. Registrar telescópio(s) e perfil  
2. Seguir schedule ExoClock  
3. Observar trânsito (guidelines ExoWorlds Spies)  
4. Reduzir (recomendado **HOPS**; AIJ aceito)  
5. Upload em https://www.exoclock.space/upload/  
6. (Opcional / projetos afiliados) reportar também à **AAVSO Exoplanet Database**

## Fontes oficiais

- https://www.exoclock.space/contribute  
- https://www.exoclock.space/  
- Guidelines observadores: https://www.exoworldsspies.com/en/observers

## Dados no BD AstroCitizen

Planet/target · BJD_TDB series · flux · flux_err · airmass · telescope/camera/filter · exposure · quality flags · ExoClock observation status  

---
