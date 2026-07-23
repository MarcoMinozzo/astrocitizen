# Atlas interno — Registro e reporte de programas observacionais

**Produto:** AstroCitizen  
**Versão:** 1.0  
**Data:** 2026-07-21  
**Objetivo:** documentar, a partir de **fontes oficiais**, como cada programa/rede recebe observações: formulários, formatos, dados obrigatórios e canais de envio.  
**Catálogo de programas:** [`../PROGRAMAS_OBSERVACIONAIS.md`](../PROGRAMAS_OBSERVACIONAIS.md)

> Este atlas é a referência para exporters (`NetworkExportPort`) e para a validação do **produto mínimo** (RN-043 / RN-080).  
> Formatos externos mudam; sempre conferir o link oficial antes de implementar um exporter.

---

## 1. Como usar

| Coluna / seção | Significado |
|----------------|-------------|
| **Rede** | Organização que recebe o dado |
| **PO-*** | Programas AstroCitizen que alimentam essa rede |
| **Canal** | Web form, upload de arquivo, API, e-mail, hub regional |
| **Formato** | Especificação oficial do pacote de dados |
| **Dados-chave** | Campos mínimos típicos |
| **Fonte oficial** | URL canônica |

**Níveis de prontidão do atlas**

| Nível | Significado |
|-------|-------------|
| **A** | Formato oficial estável, bem documentado, implementável |
| **B** | Oficial, mas regional / multi-formulário / em transição |
| **C** | Rede fraca ou reporte não padronizado; arquivo local + convenção AstroCitizen |
| **D** | Educacional / interno apenas |

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

### 3.1 AAVSO — Variable Star Observations

| | |
|--|--|
| **PO-*** | A01, A02, A03; visual F03; trânsitos também via AAVSO Exoplanet (ver 3.2) |
| **Canal** | WebObs / Submit Photometric Observations (WebObs 2.0 em rollout) |
| **Formatos oficiais** | (1) **AAVSO Extended File Format** — CCD/DSLR/PEP/CMOS; (2) **AAVSO Visual File Format** — visual/fotográfico |
| **Extensões** | `.txt`, `.csv`, `.tsv` |
| **Nível** | A |

#### Cabeçalho Extended (obrigatório)

```
#TYPE=Extended
#OBSCODE=<código AAVSO do observador>
#SOFTWARE=<nome e versão>
#DELIM=,   (ou tab / comma / ; etc.)
#DATE=JD   (ou HJD / EXCEL)
#OBSTYPE=CCD  (CCD|DSLR|PEP; CMOS reportar como CCD)
```

#### Campos de cada linha (Extended)

`STARID, DATE, MAGNITUDE, MAGERR, FILTER, TRANS, MTYPE, CNAME, CMAG, KNAME, KMAG, AIRMASS, GROUP, CHART, NOTES`

- Opcionais ausentes → `na`  
- `MAGNITUDE`: ponto decimal obrigatório; `<` para fainter-than  
- `FILTER`: V, B, R, I, TG/TB/TR, CV/CR, Sloan, etc. (lista oficial AAVSO)  
- `TRANS`: YES/NO · `MTYPE`: STD (recomendado) ou DIF  
- `CHART`: Sequence ID da tabela VSP  

#### Pré-requisitos de conta

- Observer code AAVSO (`OBSCODE`)  
- Sequências/cartas VSP quando aplicável  

#### Fontes oficiais

- https://www.aavso.org/aavso-file-format-specifications  
- https://www.aavso.org/aavso-extended-file-format  
- https://www.aavso.org/aavso-visual-file-format  
- https://www.aavso.org/webobs/  

#### Dados que AstroCitizen deve persistir (BD)

Observer code · STARID/AUID · JD/HJD midpoint · mag · magerr · filter · transform flag · comp/check · airmass · chart/sequence · software · raw observation_ids  

---

### 3.2 ExoClock (+ ponte AAVSO Exoplanet)

| | |
|--|--|
| **PO-*** | A05 |
| **Canal** | Conta ExoClock → registrar telescópios → upload de curva de luz |
| **Formato** | Arquivo de fotometria reduzida (não FITS bruto): HOPS `…for ExoClock.txt` ou subset AIJ (`BJD_TDB`, flux normalizado, erro, airmass) |
| **Nível** | A |

#### Fluxo oficial (resumo)

1. Registrar telescópio(s) e perfil  
2. Seguir schedule ExoClock  
3. Observar trânsito (guidelines ExoWorlds Spies)  
4. Reduzir (recomendado **HOPS**; AIJ aceito)  
5. Upload em https://www.exoclock.space/upload/  
6. (Opcional / projetos afiliados) reportar também à **AAVSO Exoplanet Database**  

#### Fontes oficiais

- https://www.exoclock.space/contribute  
- https://www.exoclock.space/  
- Guidelines observadores: https://www.exoworldsspies.com/en/observers  

#### Dados no BD AstroCitizen

Planet/target · BJD_TDB series · flux · flux_err · airmass · telescope/camera/filter · exposure · quality flags · ExoClock observation status  

---

### 3.3 µFUN — Microlensing

| | |
|--|--|
| **PO-*** | A06 |
| **Canal** | Coordenação por alertas µFUN / PI da campanha (historicamente e-mail + fotometria densa) |
| **Formato** | Não há um único “file format” público estável como AAVSO; tipicamente séries fotométricas + metadados de site/instrumento conforme instruções do alerta |
| **Nível** | B |

#### Política AstroCitizen

- Persistir curva completa no BD no esquema fotométrico interno  
- Export “genérico” CSV/FITS table + pacote de metadados  
- Campos mínimos: target (event ID), HJD/BJD, mag/flux, err, filter, site, telescope, observer  

#### Fonte / contexto

- Literatura do acervo: pasta `microfun/`  
- Acompanhar site/alertas µFUN vigentes na época da implementação  

---

### 3.4 MPC — Minor Planet Center (astrometria)

| | |
|--|--|
| **PO-*** | C01, C02, C04, C05; apoio A09/A10 se houver astrometria |
| **Canal** | Formulários web ADES ou cURL (`submit_xml` / `submit_psv`) — **não** e-mail para ADES |
| **Formato oficial** | **ADES** (Astrometry Data Exchange Standard): **XML** (preferido) ou **PSV** (pipe-separated). MPC1992 80-colunas obsoleto para códigos novos |
| **Validação** | Schema `submit.xsd` |
| **Nível** | A |

#### Pré-requisitos

- **Observatory code** MPC  
- Conformidade com *Guide to Minor Body Astrometry* (além do formato)  

#### Submissão (exemplos oficiais)

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

#### Dados típicos ADES (conceito)

Observatory · object designation · epoch (UTC) · RA/Dec (+ incertezas) · mag (+ banda) · catalogo de referência · modo de observação · observador/programa  

#### Fontes oficiais

- https://minorplanetcenter.net/mpcops/documentation/ades/  
- https://data.minorplanetcenter.net/iau/info/Astrometry.html  
- https://docs.minorplanetcenter.net/mpc-ops-docs/observations/command-line-submissions/  
- https://minorplanetcenter.net/submit_xml · https://minorplanetcenter.net/submit_psv  
- ADES GitHub (especificação IAU)  

#### Dados no BD AstroCitizen

MPC code · designation · epoch · RA/Dec/σ · mag/band · ADES XML/PSV artifact URI · submission ack/CurlID · status  

---

### 3.5 COBS / ICQ — Cometas (fotometria / visual)

| | |
|--|--|
| **PO-*** | A10 (fotometria); imaging E06 pode coexistir localmente |
| **Canal** | COBS web form (armazena em formato ICQ) e/ou contribuição ICQ |
| **Formato** | **ICQ 80-column** (+ extensão CCD após col. 80 desde 2002) |
| **Nível** | A |

#### Dados típicos ICQ

UT date (0.01 d) · magnitude total · método de mag · fonte das comps · instrumento (abertura, tipo, f/, exposição/mag) · diafragma, DC, cauda, PA, etc. · campos CCD extras  

#### Fontes oficiais

- https://www.cobs.si/ · https://www.cobs.si/help/icq_format/  
- http://www.icq.eps.harvard.edu/ICQFormat.html  

---

### 3.6 TNS — Transient Name Server (supernovas / AT)

| | |
|--|--|
| **PO-*** | C03 |
| **Canal** | Formulários web interativos **ou** Bulk API JSON (bots) |
| **Ambiente de teste** | https://sandbox.wis-tns.org (obrigatório para desenvolver API) |
| **Nível** | A |

#### Tipos de reporte

1. **AT-rep** (discovery): coordenadas, grupo, fonte de dados, fotometria de descoberta (**obrigatória**), última non-detection, arquivos relacionados (finding chart…)  
2. **Class-rep** (classification): espectro de suporte; prefixo AT→SN quando aplicável  

#### Formato API

JSON conforme manuais TNS 2.0 (IDs de grupo, instrumento, filtro via tabelas AUX).

#### Fontes oficiais

- https://www.wis-tns.org/  
- https://www.wis-tns.org/content/tns-getting-started  
- https://www.wis-tns.org/sites/default/files/api/tns2_manuals/TNS2.0_bulk_reports_manual.pdf  
- Dados estendidos de LC/espectros: WISeREP (https://www.wiserep.org) — TNS **não** substitui repositório de curvas longas  

#### Nota

Variáveis galácticas / novas clássicas **não** devem ir ao TNS (orientação oficial TNS).

---

### 3.7 BeSS (+ ecossistema ARAS)

| | |
|--|--|
| **PO-*** | B02, B03; B01 quando alvo Be |
| **Canal** | Upload no site BeSS (primeiro espectro validado por admins → login) |
| **Formato** | **FITS 1D** (HDU único), keywords BeSS / `BSS_*` |
| **Arquivos** | `.fits` ou archive `.zip` / `.tar.gz` ≤ 15 MB |
| **Nível** | A |

#### Requisitos científicos (especificação BeSS)

- Alvo Be do catálogo BeSS (ou contato com admins)  
- Espectro **pré-processado e calibrado em λ** (bias/dark/flat, geometria, céu, extração, calibração linear)  
- OBSERVER presente  
- Normalização / telluric / Vhelio: desaconselhados; se feitos, keywords obrigatórias  

#### Keywords (resumo)

- Identificação: `OBJNAME` **ou** `RA`+`DEC` (+ equinox/FK5)  
- Tempo: 2 entre `DATE-OBS`, `DATE-END`, `EXPTIME`  
- Site: `BSS_SITE` **ou** lat/long/elev **ou** satélite  
- Instrumento: `BSS_INST` **ou** `TELESCOP`+`DETNAM`+`INSTRUME`  
- WCS espectral: `CRVAL1`, `CDELT1`, `CRPIX1`, `CTYPE1`, `CUNIT1`, …  
- Resolução indicativa: `BSS_ESRP` / correlatos  

#### Fontes oficiais

- Spec BeSS (PDF): http://basebe.obspm.fr/basebe/Spec_spectres_BeSS_en.pdf  
- Portal BeSS: http://basebe.obspm.fr/  
- Paper BeSS: Neiner et al. (AJ)  
- ARAS: campanhas/alertas e convenções de nome de arquivo no fórum spectro-aras (complementar a BeSS)  

#### Dados no BD AstroCitizen

FITS 1D URI · header keywords · observer · site · instrument · DATE-OBS · resolution · BeSS upload status · raw frames retention note (obrigação BeSS: manter brutos)  

---

### 3.8 IOTA — Ocultações

| | |
|--|--|
| **PO-*** | D01–D04 |
| **Canal** | **Regional** (não um único formulário global) |
| **Nível** | B |

#### América do Norte / AU-NZ (exemplo)

- Formulário Excel oficial (Asteroid Report Forms, versões atualizadas)  
- Upload via **IOTA Hub** (iota-hub.com) com arquivos de suporte  
- Nomeação típica: `YYYYMMDD_AstNo_AstName_ObserverLastName_pos/neg.xls`  
- Anexos: CSV PyMovie/LiMovie/Tangra · log PYOTE/ROTE/Occular/AOTA · gráfico de curva de luz  

#### Europa (IOTA-ES)

- **SODIS** + formulário texto tipo Occult/OW (`IOTA-ES_report_*.txt`)  
- Preencher via Occult Watcher Report add-in quando possível  

#### Ásia (IOTA/EA)

- E-mail regional (`asteroid-report@…`, `lunar-report@…`) + docs PDF oficiais  

#### Lunar

- Canal distinto: http://lunar-occultations.com/iota/lunarreport.htm  

#### Fontes oficiais

- https://occultations.org/observing/reporting-observations/  
- https://www.asteroidoccultation.com/observations/Forms/AsteroidReportForms.html  
- https://asteroidoccultations.com/observations/  
- SODIS manual (IOTA-ES)  

#### Dados no BD AstroCitizen

Event ID · star · asteroid · site lat/lon/elev · timesource (GPS/VTI…) · D/R times (+σ) · pos/neg · instrument/camera · weather · analysis software · report package URI · hub region  

---

### 3.9 WDS — Washington Double Star Catalog

| | |
|--|--|
| **PO-*** | G01 |
| **Canal** | Contribuição ao USNO / maintainer WDS (medidas publicáveis) |
| **Formato** | Catálogo WDS tem layout colunar fixo; novas medidas seguem práticas USNO (contato/instruções vigentes) |
| **Nível** | B |

#### Dados típicos de uma medida

Época · ângulo de posição (°) · separação (″) · magnitudes · identificação do par (discoverer designation / WDS) · método · observatório  

#### Fontes

- https://www.astro.gsu.edu/wds/ (USNO WDS)  
- ReadMe CDS B/wds  

---

### 3.10 Redes solares

| | |
|--|--|
| **PO-*** | E03, E04, B06, I01 |
| **Canal** | Múltiplos (AAVSO Solar, BAA, ALPO, SILSO/SIDC para contagens, rádio clubs…) |
| **Nível** | B–C |

#### Política AstroCitizen (v1)

- Persistência interna completa (imagens, timestamps, instrumentação, safety checklist)  
- Exporters específicos por rede solar ativados sob demanda quando a rede alvo for escolhida no programa  
- Contagem de manchas / SID: seguir formulários da rede escolhida na implementação  

---

### 3.11 Programas sem rede externa (arquivo AstroCitizen)

| PO-* | Produto mínimo interno | Formato sugerido no BD/artefato |
|------|------------------------|--------------------------------|
| A04 clusters UBVRI | Tabela mag/cores + FITS calibrados | CSV + FITS |
| A07/A08 rápida / asteroseis | Série temporal | Tabela tempo-magnitude |
| B04–B08 | Espectro 1D / lab | FITS 1D (+ BeSS keywords se aplicável) |
| E01–E02, E05–E06, F* | Imaging / logs | FITS/TIFF + metadados sessão |
| H01 polarimetria | Stokes / pol.% | Tabela + FITS |
| I02–I04 rádio | Potência vs tempo / espectro | Tabela/HDF5 |
| J* calibração | Masters + métricas CCD | FITS masters + tabela ruído/ganho |
| K* educação | Relatório de lab | PDF/Markdown + dataset |

**Nível:** C–D — ainda assim **obrigatório** gravar no BD (RN-110).

---

## 4. Matriz de implementação (exporters)

| Exporter ID | Rede | Formato de saída | Prioridade produto |
|-------------|------|-----------------|--------------------|
| EXP-AAVSO-EXT | AAVSO | Extended text | P1 |
| EXP-AAVSO-VIS | AAVSO | Visual text | P2 |
| EXP-EXOCLOCK | ExoClock | LC txt (HOPS/AIJ-compatible) | P1 |
| EXP-MPC-ADES | MPC | ADES XML/PSV | P1 |
| EXP-COBS-ICQ | COBS | ICQ record / web fields | P3 |
| EXP-TNS-JSON | TNS | AT/Class JSON | P1 |
| EXP-BESS-FITS | BeSS | FITS 1D + BSS_* | P1 |
| EXP-IOTA-PACK | IOTA | Pacote regional (XLS/TXT+anexos) | P1 |
| EXP-WDS | WDS | Medida estruturada | P2 |
| EXP-LOCAL | — | Pacote AstroCitizen | P0 (sempre) |

---

## 5. Checklist genérico antes de exportar (RN-080)

1. Produto mínimo do PO-* atingido e versionado no BD  
2. Site, equipamento e tempo UTC consistentes  
3. Credenciais/códigos de observador presentes (OBSCODE, MPC code, TNS group…)  
4. Artefatos anexos exigidos pela rede (charts, LC plots, finding charts…)  
5. Validação contra schema/spec oficial quando existir (ADES XSD, BeSS checker, AAVSO parser…)  
6. Status `ContribuicaoRede`: rascunho → validado → exportado → enviado  

---

## 6. Lacunas conhecidas / a revalidar na implementação

| Tema | Ação |
|------|------|
| WebObs → WebObs 2.0 | Revalidar URL e API de upload AAVSO |
| IOTA Hub (2026) | Confirmar fluxo único NA vs regionais |
| µFUN | Obter instruções atuais do coordenador de campanha |
| WDS submit path | Confirmar procedimento USNO vigente |
| Solar networks | Escolher 1–2 redes alvo para P2 |
| ARAS eruptive (não-Be) | Além de BeSS: bases ARAS específicas (novae/LBV) — mapear por campanha |

---

## 7. Controle de mudanças

| Ver. | Data | Notas |
|------|------|-------|
| 1.0 | 2026-07-21 | Primeira versão do atlas a partir de fontes oficiais online |

Qualquer mudança de formato externo que quebre exporter → atualizar esta ficha + ADR em `docs/decisoes/`.
