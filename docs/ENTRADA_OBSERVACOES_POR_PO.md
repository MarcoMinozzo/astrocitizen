# Entrada de observações por programa (PO-*)

**Status:** desenho de produto (decisão de UX de dados)  
**Data:** 2026-07-21  
**Fontes:** [PROGRAMAS_OBSERVACIONAIS.md](PROGRAMAS_OBSERVACIONAIS.md), [atlas/ATLAS_REPORTE_OBSERVACOES.md](atlas/ATLAS_REPORTE_OBSERVACOES.md), [MODELO_DADOS_V1.md](MODELO_DADOS_V1.md), [WORKFLOWS.md](WORKFLOWS.md), catálogo `program_templates.json`  
**Mandato:** para **cada** PO-* definir *como* o utilizador fornece a informação observacional à plataforma — não só o formato de export.

---

## 1. Princípio

Não há 50 ecrãs distintos. Há **canais de entrada reutilizáveis** (padrões). Cada PO-* escolhe:

1. **Canal primário** de aquisição / ingestão  
2. **Metadados obrigatórios** (formulário / CLI / headers)  
3. **Produto mínimo** interno  
4. **Export** (rede), quando aplicável  

```
Canal de entrada  →  Observation + Artifact(s)  →  AnalysisProduct  →  Rede
```

Uma observação pode ter **zero imagens** (visual, rádio, timing puro) ou **muitos** FITS (fotometria, stack).

---

## 2. Canais partilhados (padrões de entrada)

| ID | Canal | O que o utilizador faz | Artefacto típico | Superfície alvo |
|----|-------|------------------------|------------------|-----------------|
| **IN-CAP** | Captura hardware | Sessão → expor (sim / Alpaca / udrv) | FITS 2D | GUI Sessão (wizard) + CLI `session capture` |
| **IN-IMP** | Import ficheiros | Arrasta / selecciona FITS, SER, AVI, CSV, HDF5… | ficheiro → ArtifactStore URI | GUI **Import** + CLI `import fits` (FITS feito; SER/CSV depois) |
| **IN-TAB** | Tabela / série | Cola ou importa CSV de fotometria, timing, rádio | CSV / pontos no BD | GUI Editor de série + CLI |
| **IN-LOG** | Log estruturado | Preenche formulário (visual, solar count, safety) | JSON + texto | GUI formulário PO-* |
| **IN-VID** | Vídeo / lucky | Importa SER/AVI ou pasta de frames | SER/AVI/FITS cube | GUI Imaging + pipeline stack |
| **IN-SPEC** | Espectro | Importa 2D (slit) ou 1D já extraído | FITS 2D/1D | GUI Espectro + CLI `analyze spectrum` |
| **IN-RAD** | Rádio | Importa potência vs tempo / espectro RF | CSV/HDF5/WAV | GUI Rádio (paralelo) |
| **IN-API** | Serviço externo | Confirma pull (meteo, efemérides, plate-solve) | JSON / FITS+WCS | Noite / analyze (já parcial) |
| **IN-PRED** | Previsão / alerta | Importa ficheiro de campanha (IOTA, µFUN, NEO) | XML/CSV/TXT | GUI Campanha |

**Regra:** todo canal grava `Observation` (metadados) + zero ou mais `artifacts`. Produtos científicos vivem em `analysis_products` / `measurement_points`.

---

## 3. Metadados comuns (todos os PO-*)

Sempre pedidos (formulário curto ou headers FITS + BD):

| Campo | Obrigatório | Notas |
|-------|-------------|-------|
| `workspace` / site | sim | SiteProfile activo |
| `program_id` (PO-*) | sim | campanha activa |
| `observed_at_utc` | sim | DATE-OBS ou relógio sessão |
| `target` (quando aplicável) | quase sempre | designação + RA/Dec se conhecido |
| `instrument` / config | sim para ciência | telescópio, câmara, filtro |
| `simulated` | sim | flag RN |
| Safety extras | só solar / laser / etc. | checklist |

---

## 4. Mapa por PO-* — como o utilizador fornece a observação

Legenda **Estado**: `feito` / `parcial` / `desenho` (ainda não na UI).

### A — Fotometria / tempo

| PO | Como o utilizador fornece | Canais | Payload mínimo | Produto | Estado |
|----|---------------------------|--------|----------------|---------|--------|
| **A01** Variáveis | Captura lights **ou** importa FITS; indica alvo + estrela comparação (x,y ou catálogo) | IN-CAP, IN-IMP | FITS + band + comp | `light_curve` → AAVSO | parcial (CLI fotometria) |
| **A02** Eruptivas | Igual A01 + cadência / duração da série | IN-CAP, IN-IMP | série densa FITS ou CSV | light_curve | desenho |
| **A03** Cefeidas/RR | Igual A01 + multi-noite (vários plans) | IN-CAP, IN-IMP | várias noites ligadas ao mesmo target | light_curve | desenho |
| **A04** Clusters UBVRI | Importa/captura por filtro; associa filtros UBVRI | IN-CAP, IN-IMP | FITS multi-filtro | tabela cores + FITS | desenho |
| **A05** Trânsitos | Captura série contínua na janela do trânsito; alvo + pred | IN-CAP, IN-IMP, IN-PRED | FITS série / LC | light_curve → ExoClock | parcial |
| **A06** Microlensing | Importa alerta µFUN + série fotométrica densa | IN-PRED, IN-CAP, IN-TAB | alerta + LC | light_curve / CSV | desenho |
| **A07** Rápida | Captura alta cadência (ou CSV de fotómetro) | IN-CAP, IN-TAB | série sub-s | time_series | desenho |
| **A08** Asteroseis | Séries longas (muitas noites) / import CSV | IN-CAP, IN-TAB | time_series longa | time_series | desenho |
| **A09** Asteroides LC | Captura com tracking; alvo MPC | IN-CAP, IN-IMP | FITS + tracking meta | light_curve | desenho |
| **A10** Cometas foto | Igual A09 + filtro/abertura coma | IN-CAP, IN-IMP | FITS + aberturas | fotometria + ICQ | desenho |

### B — Espectroscopia

| PO | Como o utilizador fornece | Canais | Payload mínimo | Produto | Estado |
|----|---------------------------|--------|----------------|---------|--------|
| **B01** Slit geral | Captura/import 2D; marca trace; calib λ (linhas / lâmpada) | IN-SPEC, IN-CAP | FITS 2D + λ | `spectrum_1d` | parcial |
| **B02** Be/BeSS | Igual B01 + object Be + keywords BeSS | IN-SPEC | FITS 1D BSS_* | spectrum → BeSS | parcial (export) |
| **B03** Novae/ARAS | Série de espectros no tempo | IN-SPEC | vários 1D | série espectral | desenho |
| **B04** Class. MK | Espectro 1D + escolha de templates | IN-SPEC, IN-LOG | 1D + tipo | classificação | desenho |
| **B05** RV educ. | Espectro + linhas de calibração | IN-SPEC | 1D + λ ref | RV table | desenho |
| **B06** Spec solar | Safety checklist + espectro solar | IN-LOG + IN-SPEC | safety + 1D/2D | linhas solares | desenho |
| **B07** Echelle | Import ordem(s) echelle | IN-SPEC | multi-order FITS | spectrum | desenho (P4) |
| **B08** Lab spectro | Flats / lâmpada / testes (sem alvo céu) | IN-CAP, IN-IMP | calib frames | métricas resolução | desenho |

### C — Astrometria / NEO / SN

| PO | Como o utilizador fornece | Canais | Payload mínimo | Produto | Estado |
|----|---------------------------|--------|----------------|---------|--------|
| **C01** NEO/MPC | Captura/import FITS; plate-solve; clica objecto | IN-CAP, IN-IMP, IN-API | FITS+WCS + (x,y) | `astrometry` → ADES | parcial |
| **C02** Follow-up | Igual C01 + modo não-sideral / taxa | IN-CAP | FITS + rates | astrometry | parcial |
| **C03** SN/TNS | Par new/ref (blink); confirma candidato | IN-IMP, IN-CAP | 2 FITS | `blink_candidate` → TNS | parcial |
| **C04** Cometas astrom | Igual C01 + tracking cometa | IN-CAP | FITS + ephem | astrometry | desenho |
| **C05** Recuperação | Import ephem Horizons + medida | IN-API, IN-IMP | ephem + FITS | astrometry | desenho |

### D — Ocultações / timing

| PO | Como o utilizador fornece | Canais | Payload mínimo | Produto | Estado |
|----|---------------------------|--------|----------------|---------|--------|
| **D01** Occ. asteróide | Import previsão IOTA + vídeo/série + GPS time | IN-PRED, IN-VID, IN-TAB | pred + LC timing | timing pack → IOTA | parcial (export pack) |
| **D02** Lunar/graze | Vídeo + station + contact times | IN-VID, IN-LOG | vídeo + contacts | timing | desenho |
| **D03** Mutuas | Timing + efemérides satélites | IN-TAB, IN-LOG | contact times | timing | desenho |
| **D04** Duplas occ. | Vídeo + análise de eventos | IN-VID | vídeo + measures | timing + dupla | desenho |

### E — Sistema Solar imaging

| PO | Como o utilizador fornece | Canais | Payload mínimo | Produto | Estado |
|----|---------------------------|--------|----------------|---------|--------|
| **E01** Lua | SER/AVI/FITS + stack | IN-VID, IN-IMP | frames | stacked image | desenho |
| **E02** Planetas | Lucky imaging (SER) | IN-VID | SER | stacked | desenho |
| **E03** Sol WL | **Checklist safety** + FITS/imagem + contagem (auto/manual) | IN-LOG + IN-IMP | safety + image | `solar_sunspots` | parcial |
| **E04** Sol Hα | Safety + filtro Hα + imagem | IN-LOG + IN-IMP | safety + image | solar activity | desenho |
| **E05** Eclipses | Timing contacts + imaging | IN-LOG + IN-IMP | times + images | timing+image | desenho |
| **E06** Cometas img | Tracking + frames | IN-CAP, IN-IMP | FITS | image pack | desenho |

### F — Deep-sky / visual

| PO | Como o utilizador fornece | Canais | Payload mínimo | Produto | Estado |
|----|---------------------------|--------|----------------|---------|--------|
| **F01** Deep-sky | LRGB/Ha frames + calib | IN-CAP, IN-IMP | FITS set | stacked LRGB | desenho |
| **F02** Messier | Imaging **ou** log visual do objecto | IN-IMP **ou** IN-LOG | image ou log | archive / log | desenho |
| **F03** Visual | **Só formulário** (sem CCD): objecto, condições, descrição | IN-LOG | log JSON/texto | visual_log | desenho |
| **F04** Asterismos | Planner + log de reconhecimento | IN-LOG | checklist céu | log | desenho |

### G / H — Duplas / polarimetria

| PO | Como o utilizador fornece | Canais | Payload mínimo | Produto | Estado |
|----|---------------------------|--------|----------------|---------|--------|
| **G01** Duplas | Imagem **ou** micrómetro (ângulo/separação manual) | IN-IMP, IN-LOG | PA, sep, epoch | double_measure | desenho |
| **G02** Speckle | Cubo/speckle frames | IN-IMP | cube | speckle product | desenho (P4) |
| **H01** Polarimetria | Frames em ângulos de polarizador | IN-CAP, IN-IMP | set polar | Stokes table | desenho (P4) |

### I — Rádio (não é imagem óptica)

| PO | Como o utilizador fornece | Canais | Payload mínimo | Produto | Estado |
|----|---------------------------|--------|----------------|---------|--------|
| **I01** Sol rádio | Série potência vs tempo (SDR/CSV) | IN-RAD | CSV/HDF5 | radio_timeseries | desenho |
| **I02** 21 cm | Espectro RF / waterfall | IN-RAD | espectro | radio_spectrum | desenho |
| **I03** Contínuo | Drift scan / pointing logs | IN-RAD, IN-LOG | scan | radio_scan | desenho |
| **I04** Lab VHF | Igual I01–I03 + notas de construção | IN-RAD, IN-LOG | série + lab notes | radio + report | desenho |

### J — Calibração / site

| PO | Como o utilizador fornece | Canais | Payload mínimo | Produto | Estado |
|----|---------------------------|--------|----------------|---------|--------|
| **J01** CCD gain/noise | Bias/dark/flat de laboratório | IN-CAP, IN-IMP | masters set | calibration metrics | parcial (masters) |
| **J02** Seeing/FWHM | Lights + medida FWHM (auto) | IN-CAP, IN-IMP | FITS | seeing series | desenho (template) |
| **J03** Masters rotina | Igual J01 campanha | IN-CAP, IN-IMP | bias/dark/flat | CalibrationMaster | parcial |
| **J04** Foco/colimação | Frames de teste + notas | IN-CAP, IN-LOG | FITS + log | focus report | desenho (template) |
| **J05** Meteo site | Pull API **ou** entrada manual thresholds/snapshot | IN-API, IN-LOG | meteo JSON | meteo snapshot | parcial (Noite) |

### K — Educação

| PO | Como o utilizador fornece | Canais | Payload mínimo | Produto | Estado |
|----|---------------------------|--------|----------------|---------|--------|
| **K01** Lab CCD | Dataset exemplo + passos guiados | IN-IMP, IN-LOG | FITS lab + workbook | lab report | desenho |
| **K02** Mini espectro | Igual B01 em modo lab | IN-SPEC | 2D/1D | lab spectrum | desenho (template) |
| **K03** Mini rádio | Igual I* em modo lab | IN-RAD | CSV | lab radio | desenho |
| **K04** Observatório escolar | Checklist projecto (não noite única) | IN-LOG | formulário projecto | project dossier | desenho (template) |

> Templates **J02, J04, K02, K04** estão em PROGRAMAS_OBSERVACIONAIS mas podem faltar no `program_templates.json` — incluir no seed quando se implementar o canal.

---

## 5. Superfícies de UI necessárias (agrupadas)

Em vez de 50 apps, **7 superfícies**:

| Superfície | Serve PO-* | Entrada |
|------------|------------|---------|
| **Sessão / Captura** | A, B, C, E, F, G, H, J | IN-CAP |
| **Importador** | quase todos | IN-IMP / IN-VID / IN-RAD |
| **Fotometria** | A* | pontos, comp stars |
| **Espectro** | B* | trace, λ |
| **Astrometria / Blink** | C* | solve + click |
| **Timing / Occultation** | D* | pred + vídeo + contacts |
| **Log / Safety / Visual / Solar count** | E03–04, F03–04, G01 manual, K* | IN-LOG |

**Noite** (já existe) alimenta J05 + planeamento, não substitui captura científica.

---

## 6. CLI espelho (contrato mínimo a estabilizar)

| Família | Comandos alvo |
|---------|----------------|
| Import genérico | `astrocitizen import fits\|csv\|ser\|radio …` |
| Captura | `session capture` (existe) |
| Fotometria | `analyze photometry` (existe) |
| Espectro | `analyze spectrum` (existe) |
| Astrometria | `analyze plate-solve` + `astrometry` (existe) |
| Blink | `analyze blink` (existe) |
| Solar | `analyze sunspots` (existe) |
| Visual log | `observe log-visual` (a criar) |
| Rádio | `analyze radio` (a criar) |
| Occultation | `analyze occultation` (a criar) |

---

## 7. Prioridade de implementação dos canais

| Ordem | Canal / superfície | Desbloqueia |
|-------|--------------------|-------------|
| 1 | **Import FITS** (GUI + CLI) | ✅ `import fits` + painel Import |
| 2 | **CRUD Site/Programa/Alvo na GUI** | metadados comuns |
| 3 | **Wizard Sessão** | IN-CAP usável no desktop |
| 4 | **Editor visual log + solar form** | F03, E03 completo |
| 5 | **Timing/IOTA import previsão + vídeo** | D01 |
| 6 | **Rádio CSV/HDF5** | I* |
| 7 | Restantes especializações (speckle, polar, echelle) | P4 |

---

## 8. Decisões fechadas neste documento

1. **Observação ≠ só imagem.** Visual, rádio, timing e logs são entradas de primeira classe.  
2. **PO-* escolhe canais**, não inventa formato de BD novo — reutiliza Observation / Artifact / AnalysisProduct.  
3. **Produto mínimo** (RN-043) valida se a entrada foi suficiente antes do export.  
4. **Safety solar** é entrada obrigatória (já no CLI sunspots); GUI deve espelhar.  
5. Próximo passo de engenharia recomendado: implementar **IN-IMP (import FITS)** + formulários CRUD na GUI, depois wizard Sessão.

---

## 9. Relação com o atlas de redes

A entrada (este doc) é **a montante** do [ATLAS_REPORTE_OBSERVACOES.md](atlas/ATLAS_REPORTE_OBSERVACOES.md):

- Aqui: *como o humano entrega dados ao AstroCitizen*  
- Atlas: *como o AstroCitizen entrega dados à rede*

Ambos são necessários por PO-*.

---

## Histórico

| Ver. | Data | Nota |
|------|------|------|
| 1.0 | 2026-07-21 | Mapa inicial 9 canais + tabela de todos os PO-* do catálogo / programas |
