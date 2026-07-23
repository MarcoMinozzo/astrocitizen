# Backlog do produto — AstroCitizen

**Versão:** 1.0  
**Data:** 2026-07-21  
**Estado:** Fase 1 — implementação · **S0–S5 concluídos** · meteo hourly/radar + painel Noite · **AC-075/076** empacote `.exe`  
**Fontes:** escopo, RN-*, PO-*, arquitetura, persistência, stack  

---

## Como usar este backlog

| Campo | Significado |
|-------|-------------|
| **Épico** | Entrega grande de valor |
| **Item** | Unidade implementável |
| **Prioridade** | P0 (fundação) … P4 (avançado) |
| **Estimativa** | S ≤3d · M 1–2 sem · L 3–6 sem · XL >6 sem |
| **Dependências** | Itens que bloqueiam |

**Definição de pronto (DoD) geral:** testes · persistência no BD quando houver resultado · docs mínimas · Linux e Windows quando aplicável a UI/adapters · **escolhas técnicas alinhadas a D-010** (otimização / recursos).

**DoD Desktop (obrigatório):** no final do dia o utilizador Windows deve ter um **executável `.exe` que funciona bem** (arrancar, modo simulador, fluxos críticos sem depender de `python` instalado). Empacote via PyInstaller (padrão sbig-suite) ou equivalente; CI Windows gera e smoke-testa o artefacto. Ver AC-075…077.

**Princípio transversal (D-010):** toda solução proposta deve maximizar **otimização técnica** e **uso eficiente de recursos computacionais** (CPU, RAM, I/O, processos, latência crítica), sem comprometer corretude nem o DoD Desktop/Windows.

---

## Mapa de épicos

| Épico | Nome | Prioridade |
|-------|------|------------|
| E0 | Fundação do repositório e skeleton | P0 |
| E1 | Persistência e ArchivePort | P0 |
| E2 | Domínio core (Site, Equipamento, Programa) | P0 |
| E3 | Planning (efemérides, meteo, programa diário) | P1 |
| E4 | Observatory ports (câmera, montagem, focuser) | P1 |
| E5 | Sessão e registro de observações | P1 |
| E6 | Redução / calibração | P1 |
| E7 | UI shell + CLI | P1 |
| E8 | Templates PO-* onda P1 | P1–P2 |
| E9 | Análise fotométrica e AAVSO | P2 |
| E10 | Análise espectroscópica e ARAS | P2 |
| E11 | Astrometria, NEO/MPC, supernovas | P2 |
| E12 | Ocultações IOTA | P2 |
| E13 | Imaging / solar / deep-sky | P2–P3 |
| E14 | Contribuição multi-rede | P2 |
| E15 | Templates PO-* ondas P2–P4 | P2–P4 |
| E16 | Rádio cidadão | P3 |
| E17 | Observatório avançado (cúpula, remoto) | P3–P4 |
| E18 | Educação / labs | P3 |
| E19 | Base de conhecimento interna + RAG | P2–P3 |

---

## E0 — Fundação do repositório e skeleton

| ID | Item | Pri | Est | Dep | Notas |
|----|------|-----|-----|-----|-------|
| AC-001 | Skeleton Python (src layout, pyproject, lint/test) | P0 | S | — | ✅ S0 — pacote `astrocitizen` 0.0.1 |
| AC-002 | Módulos vazios dos bounded contexts | P0 | S | AC-001 | ✅ S0 — + ports hexagonais |
| AC-003 | CI GitHub Actions (Linux + Windows, pytest) | P0 | S | AC-001 | ✅ S0 — `.github/workflows/ci.yml` |
| AC-004 | Documentação de contribuição / CONTRIBUTING | P0 | S | — | ✅ S0 — `CONTRIBUTING.md` |

---

## E1 — Persistência (RN-110…116)

| ID | Item | Pri | Est | Dep | Notas |
|----|------|-----|-----|-----|-------|
| AC-010 | `ArchivePort` + modelo relacional v1 | P0 | M | AC-002 | ✅ S1 — Protocol expandido; ver [MODELO_DADOS_V1.md](MODELO_DADOS_V1.md) |
| AC-011 | Adapter SQLite + migrações | P0 | M | AC-010 | ✅ S1 — `SqliteArchive` + `schema_migrations` |
| AC-012 | `ArtifactStorePort` (FITS em disco + URI no BD) | P0 | S | AC-010 | ✅ S1 — `LocalArtifactStore` (URI file://) |
| AC-013 | Soft-delete + auditoria básica | P0 | S | AC-011 | ✅ S1 — `deleted_at` + `audit_log` |
| AC-014 | Flag `simulada` e filtros de query | P0 | S | AC-011 | ✅ S1 — `observations.simulated` |
| AC-015 | Caminho PostgreSQL (mesmo port) | P3 | M | AC-011 | Evolução |

---

## E2 — Domínio core

| ID | Item | Pri | Est | Dep | Notas |
|----|------|-----|-----|-----|-------|
| AC-020 | Entidade Site / SiteProfile (RN-001…004) | P0 | S | AC-010 | ✅ S1 |
| AC-021 | Inventário de Equipamento + ConfiguraçãoInstrumental | P0 | M | AC-020 | ✅ S1 |
| AC-022 | ProgramaObservacional + estados (RN-040…047) | P0 | M | AC-010 | ✅ S1 — estados draft/active/paused/archived |
| AC-023 | Catálogo de templates PO-* (metadados JSON/YAML) | P0 | M | AC-022 | ✅ S1 — 49 templates JSON + seed |
| AC-024 | Repositórios de domínio (via ArchivePort) | P0 | M | AC-011 | ✅ S1 — métodos no SqliteArchive |

---

## E3 — Planning

| ID | Item | Pri | Est | Dep | Notas |
|----|------|-----|-----|-----|-------|
| AC-030 | `EphemerisPort` + adapter Astropy (AltAz) | P1 | M | AC-020 | ✅ S2 — `AstropyEphemeris` |
| AC-031 | Adapter Astroquery (SIMBAD, Horizons, MPC) | P1 | M | AC-030 | ✅ S2 — SIMBAD opcional `[sky]`; Horizons/MPC depois |
| AC-032 | `MeteoPort` + adapter API + manual (RN-020…024) | P1 | M | AC-020 | ✅ S2 — Open-Meteo + ManualMeteo; ✅ hourly + dew/precip_prob + `RadarPort`/RainViewer |
| AC-033 | Snapshot meteo/efemérides no BD (RN-113) | P1 | S | AC-011, AC-032 | ✅ S2 — tabelas + persistência |
| AC-034 | Geração ProgramaDiario (RN-050…056) | P1 | L | AC-022, AC-030, AC-032 | ✅ S2 — `GenerateDailyPlan` (RN-056 freeze → S3) |
| AC-035 | Edição manual do diário + motivos inviável | P1 | M | AC-034 | ✅ S2 — `EditDailyPlan` + CLI |
| AC-036 | Validação de equipamento no plano (RN-030…035) | P1 | M | AC-021, AC-034 | ✅ S2 |
| AC-037 | Resolução de conflitos multi-programa (prioridade) | P1 | M | AC-034 | ✅ S2 |

---

## E4 — Observatory ports (hardware)

| ID | Item | Pri | Est | Dep | Notas |
|----|------|-----|-----|-----|-------|
| AC-040 | `CameraPort` + SimulatorCamera | P1 | M | AC-002 | ✅ S3 — `SimulatorCamera` |
| AC-041 | Adapter Alpaca Camera (Alpyca) | P1 | L | AC-040 | ✅ S3 — stub + extra `[alpaca]`; Omni depois |
| AC-042 | Adapter SBIG udrv (integração sbig-suite) | P1 | L | AC-040 | ✅ S3 — stub; repo `sbig-suite` |
| AC-043 | `MountPort` + Simulator + Alpyca Telescope | P1 | L | AC-002 | ✅ S3 — sim + stub Alpaca |
| AC-044 | `FocuserPort` + Alpyca Focuser | P1 | M | AC-002 | ✅ S3 — sim + stub Alpaca |
| AC-045 | FilterWheel / ObservingConditions (Alpaca) | P2 | M | AC-043 | |
| AC-046 | Factory de backends (udrv \| alpaca \| sim) | P1 | S | AC-040…044 | ✅ S3 |
| AC-047 | Omni Simulator / docs setup Linux+Windows | P1 | M | AC-043 | ✅ S3 — [HARDWARE_SIMULATOR.md](HARDWARE_SIMULATOR.md) |

---

## E5 — Sessão e registro

| ID | Item | Pri | Est | Dep | Notas |
|----|------|-----|-----|-----|-------|
| AC-050 | Caso de uso ExecutarSessao (snapshot diário) | P1 | M | AC-034 | ✅ S3 — RN-056 |
| AC-051 | Registrar Observacao → BD + FITS (RN-060…064) | P1 | M | AC-012, AC-050 | ✅ S3 |
| AC-052 | Headers FITS ricos (site, alvo, meteo, PO-*) | P1 | S | AC-051 | ✅ S3 |
| AC-053 | Política de falha de instrumento (RN-092) | P1 | S | AC-050 | ✅ S3 |
| AC-054 | Aquisição ad hoc + associação posterior a programa | P2 | S | AC-051 | ✅ inicio — `import fits` (IN-IMP) + painel Import |

---

## E6 — Redução / calibração

| ID | Item | Pri | Est | Dep | Notas |
|----|------|-----|-----|-----|-------|
| AC-060 | Masters bias/dark/flat versionados no BD | P1 | M | AC-012 | ✅ S4 — `BuildMaster` |
| AC-061 | Aplicar calibração → ProdutoAnalise | P1 | M | AC-060 | ✅ S4 — `ApplyCalibration` |
| AC-062 | Viewer FITS básico (stretch, ROI, hist) | P1 | M | AC-007 | ✅ `fits_stats` + stretch · GUI Viewer em Analisar (U4) |
| AC-063 | Stack / align básico | P2 | M | AC-061 | |

---

## E7 — UI shell + CLI

| ID | Item | Pri | Est | Dep | Notas |
|----|------|-----|-----|-----|-------|
| AC-070 | CLI: site, programas, plan, session (esqueleto) | P1 | M | AC-001 | ✅ S4 — + reduce/analyze/gui |
| AC-071 | GUI shell PySide6 (navegação por módulos) | P1 | L | AC-001 | ✅ S4 — `astrocitizen gui` · tema ops + brand bar |
| AC-072 | Telas: Sites, Equipamento, Programas | P1 | M | AC-071, E2 | ✅ CRUD Sites/Programas/Alvos + **Equipamento/Setup** |
| AC-073 | Telas: Programa diário, Sessão, Arquivo | P1 | L | AC-071, E3, E5 | ✅ Sessao wizard IN-CAP · plano/arquivo listas |
| AC-073a | Painel **Noite**: forecast hourly + radar + estado do plano | P1 | M | AC-071, AC-032 | ✅ + **Gerar plano** · badge VIABLE · fetch async |
| AC-074 | Painel gestão multi-programa | P2 | M | AC-071, AC-022 | |
| AC-075 | Empacote **Windows `.exe`** (PyInstaller onedir/onefile) | P1 | M | AC-071 | ✅ — `scripts/build_pyinstaller.sh` · [packaging/README.md](packaging/README.md) |
| AC-076 | CI: build + smoke test do `.exe` (simulator) em `windows-latest` | P1 | S | AC-075, AC-003 | ✅ — job `windows-exe` + artefact `astrocitizen-windows` |
| AC-077 | Instalador Windows opcional (NSIS/MSI) + nota drivers (udrv/Alpaca) | P2 | M | AC-075 | Assinatura código depois |
| AC-078 | Empacote Linux (AppImage ou PyInstaller) paridade | P2 | M | AC-071 | |

---

## E8 — Templates PO-* onda P1 (oficiais)

Instanciar templates + fluxos mínimos (planejar → registrar → produto mínimo).

| ID | Template | Pri | Est | Dep |
|----|----------|-----|-----|-----|
| AC-080 | PO-J01/J03/J05 Calibração + meteo site | P1 | M | E3, E6 | ✅ S5 — workflows P1 |
| AC-081 | PO-A01 Variáveis (AAVSO) — esqueleto programa | P1 | M | E2, E9 | ✅ S5 — workflow + fotometria + export |
| AC-082 | PO-A05 Trânsitos — esqueleto | P1 | M | E9 | ✅ export ExoClock LC |
| AC-083 | PO-B01 Espectroscopia slit — esqueleto | P1 | M | E10 | ✅ workflow + `analyze spectrum` + BeSS `--product` |
| AC-084 | PO-B02/B03 Be/ARAS — esqueleto | P1 | M | E10 | ✅ BeSS FITS 1D export |
| AC-085 | PO-C01/C02 NEO/MPC — esqueleto | P1 | M | E11 | ✅ workflow + `analyze astrometry` + MPC `--product` |
| AC-086 | PO-C03 Supernovas blink — esqueleto | P1 | M | E11 | ✅ workflow + `analyze blink` + TNS `--product` |
| AC-087 | PO-D01 Ocultações IOTA — esqueleto | P1 | M | E12 | ✅ pacote IOTA-ES |
| AC-088 | PO-E03 Sol manchas — esqueleto | P1 | M | E13 | ✅ + GUI Observar solar |

---

## E9 — Fotometria e AAVSO

| ID | Item | Pri | Est | Dep | Notas |
|----|------|-----|-----|-----|-------|
| AC-090 | Detecção / centroide | P2 | M | E6 | ✅ S5 — inicio (centroid) |
| AC-091 | Fotometria de abertura + diferencial | P2 | L | AC-090 | ✅ S5 — inicio |
| AC-092 | Curva de luz → BD (pontos) | P2 | M | AC-091, E1 | ✅ S5 — measurement_points |
| AC-093 | Export AAVSO | P2 | M | AC-092, E14 | ✅ Extended com JD · `contribute aavso` · WebObs manual |
| AC-094 | Templates A02–A04, A09 | P2 | M | AC-091 | |

---

## E10 — Espectroscopia e ARAS

| ID | Item | Pri | Est | Dep | Notas |
|----|------|-----|-----|-----|-------|
| AC-100 | Extração espectro 1D | P2 | L | E6 | |
| AC-101 | Calibração λ | P2 | L | AC-100 | |
| AC-102 | Medidas de linha / EW | P2 | M | AC-101 | inicio via `spectrum-report` (extrema) |
| AC-103 | Persistência espectro + produto no BD | P2 | M | AC-101 | |
| AC-104 | Export ARAS/BeSS | P2 | M | E14 | ✅ BeSS FITS 1D · `contribute bess` |
| AC-105 | Templates B04–B06 | P2–P3 | M | AC-102 | |
| AC-106 | Interpretacao espectral assistida (linhas / multi-epoca / pista classe) | P1 | M | AC-100 | ✅ deterministico · [ANALISE_ESPECTRAL_ASSISTIDA.md](ANALISE_ESPECTRAL_ASSISTIDA.md) · CLI `spectrum-report` |
| AC-107 | Narrativa LLM sobre `spectrum_report` (opt-in) | P2 | M | AC-106 | Pos-medidas; citar FEATURES; sem inventar linhas |
| AC-108 | Provider LLM pluggable + modo offline (desligado = AC-106 sozinho) | P2 | M | AC-107 | Local e/ou API; credenciais fora do BD |
| AC-109 | Guardrails + testes de grounding (spectrum + passagens RAG) | P2 | M | AC-107, AC-194 | Rejeitar claims fora do relatorio/corpus |

---

## E11 — Astrometria / NEO / SN

| ID | Item | Pri | Est | Dep | Notas |
|----|------|-----|-----|-----|-------|
| AC-110 | Plate-solve / WCS (integração externa) | P2 | L | E6 | ✅ `analyze plate-solve` · solve-field / nova / synthetic |
| AC-111 | Medidas astrométricas → BD | P2 | M | AC-110 | ✅ `astrometry` + GUI Analisar (x,y→RA/Dec) |
| AC-112 | Export MPC | P2 | M | E14 | ✅ ADES PSV + `contribute mpc` (dry-run default) |
| AC-113 | Blink / diff imaging | P2 | M | E6 | |
| AC-114 | Tracking não-sideral (apoio NEO/cometa) | P2 | L | E4 | |

---

## E12 — Ocultações IOTA

| ID | Item | Pri | Est | Dep | Notas |
|----|------|-----|-----|-----|-------|
| AC-120 | Import previsão IOTA / arquivo | P2 | M | E3 | ✅ `import prediction` · produto occultation_prediction |
| AC-121 | Export pacote IOTA-ES / Hub | P2 | M | E14 | ✅ `contribute iota` |
| AC-121 | Aquisição timed + timestamps | P2 | L | E5 | |
| AC-122 | Redução de contato + relatório | P2 | L | AC-121 | ✅ suggest D/R a partir de LC (heurística); relatório completo aberto |
| AC-123 | Templates D02–D04 | P3 | M | AC-122 | |

---

## E13 — Imaging / solar / deep-sky

| ID | Item | Pri | Est | Dep | Notas |
|----|------|-----|-----|-----|-------|
| AC-130 | Pipeline lunar/planetário (lucky/stack) | P2 | L | E6 | |
| AC-131 | Deep-sky sequence LRGB básica | P2 | L | E6 | |
| AC-132 | Modo solar + avisos de segurança | P2 | M | E5 | ✅ inicio — checklist obrigatorio em `analyze sunspots` |
| AC-133 | Templates E/F restantes | P3 | M | AC-130 | |

---

## E14 — Contribuição multi-rede

| ID | Item | Pri | Est | Dep | Notas |
|----|------|-----|-----|-----|-------|
| AC-140 | Modelo ContribuicaoRede + status | P2 | S | E1 | ✅ `network_submissions` schema v5 |
| AC-141 | Validação produto mínimo por PO-* | P2 | M | AC-140 | |
| AC-142 | Segredos locais (credenciais) | P2 | S | AC-140 | ✅ `credentials.json` local |
| AC-143 | Painel de envios pendentes | P2 | M | E7 | ✅ GUI **Contribute** + CLI list |
| AC-144 | TNS Bulk API AT-rep | P1 | M | AC-140 | ✅ sandbox + dry-run · `contribute tns` |
| AC-145 | Export ExoClock LC | P1 | M | AC-140 | ✅ `contribute exoclock` |

---

## E15 — Templates PO-* ondas P2–P4

| ID | Item | Pri | Est | Dep | Notas |
|----|------|-----|-----|-----|-------|
| AC-150 | Onda P2 completa (ver PROGRAMAS_OBSERVACIONAIS) | P2 | XL | E8–E14 | |
| AC-151 | Microlensing PO-A06 | P2 | L | E9 | |
| AC-152 | Duplas PO-G01 | P2 | M | E6 | ✅ `observe log-double` · produto double_measure · GUI Observar |
| AC-153 | Onda P3 (rápido, asteroseis, visual, rádio prep) | P3 | XL | | |
| AC-154 | Onda P4 (echelle, speckle, polarimetria) | P4 | XL | | ✅ entrada ENTRADA#7; redução profunda aberta |

---

## E16 — Rádio cidadão

| ID | Item | Pri | Est | Dep | Notas |
|----|------|-----|-----|-----|-------|
| AC-160 | Backend rádio (potência / série temporal) | P3 | L | E1 | ✅ `import radio` · produto radio_timeseries · GUI Radio |
| AC-161 | Templates PO-I01…I04 | P3 | L | AC-160 | ✅ spectrum/scan CSV + workflows + GUI modos + lab_notes |

---

## E17 — Observatório avançado

| ID | Item | Pri | Est | Dep | Notas |
|----|------|-----|-----|-----|-------|
| AC-170 | Dome / Switch / Safety (Alpaca) | P3 | L | E4 | |
| AC-171 | Sessão remota / orquestração | P4 | XL | AC-170 | |

---

## E18 — Educação

| ID | Item | Pri | Est | Dep | Notas |
|----|------|-----|-----|-----|-------|
| AC-180 | Modo lab / roteiros guiados | P3 | M | E7 | PO-K* |
| AC-181 | Datasets de exemplo + simulador completo | P2 | M | E4, E1 | |

---

## E19 — Base de conhecimento interna + RAG

Epico aberto: corpus interno versionado → retrieval → (opcional) MCP/LLM ancorado.  
Doc: [EPICO_E19_BASE_CONHECIMENTO_RAG.md](EPICO_E19_BASE_CONHECIMENTO_RAG.md)  
**Processo de referencia:** motorsport-agent *Knowledge Base MCP Coaching* (fases KB-0…5, trust tiers, FTS→vector, gold QA).

| ID | Item | Pri | Est | Dep | Notas |
|----|------|-----|-----|-----|-------|
| AC-190 | Scaffold `knowledge-base/` (catalog, taxonomy, manifest, licenses, chunk template) | P2 | S | — | ✅ KB-0 `knowledge-base/` + validate_kb_scaffold |
| AC-191 | Modelo `knowledge_documents` / `knowledge_chunks` (+ trust_tier, hash, source_id) | P2 | M | E1, AC-190 | Schema dedicado (nao misturar com FITS) |
| AC-192 | Pipeline de ingestao T3: `docs/` + atlas (offline; sem PDF em runtime) | P2 | L | AC-191 | Chunk 300–800 tokens |
| AC-193 | Retriever lexical FTS (SQLite FTS5 Desktop) + CLI `knowledge search` | P2 | M | AC-192 | Util sem embeddings |
| AC-194 | `RetrieverPort` + filtros (PO-*, rede, topic, lang) | P2 | M | AC-193 | Porta hexagonal |
| AC-195 | Embeddings locais + indice hibrido (RRF lexical/vector) | P2 | L | AC-193 | Preferir on-device; D-010 |
| AC-196 | Assistente Ajuda grounded (CLI/GUI) so com citacoes | P2 | L | AC-194 | LLM opcional; retrieval obrigatorio |
| AC-197 | MCP read-only (`kb_search`, `kb_get_chunk`, `kb_list_sources`) | P2 | M | AC-194 | Contrato tipo Vectron; rate limit |
| AC-198 | Glossario astro/redes/PO sync → chunks + UI | P2 | M | AC-192 | Analogao glossario piloto |
| AC-199 | Gold questions + eval citation rate (≥80% factuais) | P2 | M | AC-193 | DoD mensuravel (BL-KB-QA*) |
| AC-200 | Ligacao spectrum: RAG + AC-107 (explicar relatorio com corpus ARAS/BeSS) | P2 | M | AC-107, AC-194 | Caso de uso piloto KB-5 |

---

## Ordem de sprints sugerida (primeiros 6)

| Sprint | Foco | Itens |
|--------|------|-------|
| S0 | Skeleton + CI | AC-001…004 |
| S1 | BD + Site + Equipamento + Programas | AC-010…024 ✅ |
| S2 | Efemérides + Meteo + ProgramaDiario | AC-030…037 ✅ |
| S3 | Camera/Mount/Focuser sim + Sessão + FITS | AC-040…053 ✅ |
| S4 | Calibração + GUI/CLI shell | AC-060…073 ✅ |
| S5 | Templates P1 esqueleto + 1 análise ponta a ponta (ex.: variáveis) | AC-080…081, início E9 ✅ |

---

## Fora do backlog de produto (não fazer neste repo)

- Fork ou merge do código `sbig-suite`  
- Redistribuir Universal Driver SBIG  
- CAD / obra civil de observatório  
- Cursos teóricos de astrofísica como produto  

---

## Rastreabilidade

| Tema | Documento |
|------|-----------|
| Regras RN-* | ESCOPO_GERAL_E_REGRAS_DE_NEGOCIO.md |
| Programas PO-* | PROGRAMAS_OBSERVACIONAIS.md |
| Arquitetura | ARQUITETURA.md |
| BD | PERSISTENCIA_E_BANCOS.md |
| Stack | STACK_TECNOLOGICA.md |
| Atlas de reporte | atlas/ATLAS_REPORTE_OBSERVACOES.md |
| Testes hardware / campo | TEST_BACKLOG.md |
