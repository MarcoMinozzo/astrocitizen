# Avalia��o de stack � Motorsport Agent ? AstroCitizen

**Vers�o:** 1.0  
**Data:** 2026-07-21  
**Atualização Desktop:** ver [COMPARACAO_DESKTOP_TAURI_VS_PYSIDE.md](COMPARACAO_DESKTOP_TAURI_VS_PYSIDE.md) e D-009.4-rev — **PySide6**, não Tauri+sidecar.

**Status:** avalia��o + decis�o de produto (D-009)  
**Fontes:** `~/motorsport-agent` � `~/client-motorsport-agent` � [ARQUITETURA_SAAS_DESKTOP.md](ARQUITETURA_SAAS_DESKTOP.md) � [STACK_TECNOLOGICA.md](STACK_TECNOLOGICA.md)

---

## 1. Resumo executivo

| Pergunta | Veredito |
|----------|----------|
| Usar o **mesmo stack SaaS** do motorsport-agent? | **Sim** � FastAPI + Next.js + PostgreSQL (DBaaS) + object storage |
| O **cliente Tauri** resolve o Desktop AstroCitizen? | **Parcialmente** � excelente para sync/auth/offline; **insuficiente sozinho** para controle de observat�rio (Python/Astropy/Alpyca/udrv) |
| Bancos n�o/semi estruturados? | **Sim, modelar explicitamente** � JSONB + object store + Parquet (s�ries) |
| Todos os BDs como **BDaaS**? | **Sim em produ��o/SaaS**; Desktop mant�m **SQLite local** (edge, offline) |

**Princ�pio:** reutilizar o *padr�o de plataforma* do Motorsport (API + dashboard + cliente edge + DBaaS), adaptando o runtime de dom�nio cient�fico/astron�mico e o lado de hardware.

---

## 2. Stack Motorsport (baseline analisado)

### 2.1 Plataforma (`motorsport-agent`)

| Camada | Tecnologia |
|--------|------------|
| API | **FastAPI**, Pydantic v2, Uvicorn |
| ORM / migra��es | **SQLAlchemy 2** + **Alembic** |
| BD relacional | **PostgreSQL** (dev Docker; prod ? **DBaaS**) |
| Fallback CI/dev | SQLite |
| Dashboard | **Next.js 16**, React 19, Tailwind, TypeScript |
| Dom�nio cient�fico | **Python** (pandas, numpy, pipelines CLI) |
| Artefatos grandes | **Filesystem** `storage/ws_*` (evolu��o: object storage) |
| Auth | JWT (cookie web + Bearer cliente) |
| Jobs | Background / subprocess cient�fico |
| Observabilidade | Prometheus metrics, logs |

Documenta��o de refer�ncia no motorsport: *Migra��o � PostgreSQL DBaaS*, *Produ��o e Deploy na Nuvem*, *architecture_overview.md*.

### 2.2 Cliente desktop (`client-motorsport-agent` / `tauri-client`)

| Camada | Tecnologia |
|--------|------------|
| Shell | **Tauri 2** |
| UI | **React** + TypeScript + Tailwind + Zustand |
| Backend nativo | **Rust** (tokio, reqwest, notify) |
| Persist�ncia local | **SQLite** (`rusqlite`) � fila offline |
| Sync | Watch de ficheiros ? upload multipart ? API `/api/client/v1/*` |
| UX | System tray, autostart, settings, hist�rico |

Papel do Tauri no motorsport: **agente de edge** (capturar ficheiros locais, fila offline, sync com SaaS) � **n�o** � o motor cient�fico.

---

## 3. Mapeamento Motorsport ? AstroCitizen

| Motorsport | AstroCitizen (alvo) | Fit |
|------------|---------------------|-----|
| Dashboard Next.js | **SaaS Web** � workspace, programas, planejamento, arquivo, an�lise, export | ? Alto |
| FastAPI + Postgres | **SaaS API** � auth, sync, ArchivePort, jobs de redu��o | ? Alto |
| `storage/ws_*` | Object store BDaaS + URI no BD (FITS, plots, exports) | ? Alto (melhorar desde o in�cio) |
| Pipeline Python cient�fico | Redu��o / fotometria / espectro (Astropy, photutils�) | ? Alto |
| Tauri client | **Desktop sync + shell** � pull plano, push obs, fila offline | ? Alto |
| Watch `.ld`/`.ibt` | Watch FITS locais / pasta de aquisi��o | ? M�dio |
| � | **Runtime observat�rio** (Alpyca, udrv, sess�o ao vivo) | ?? Gap � ver �4 |

---

## 4. Avalia��o Desktop: Tauri resolve?

### 4.1 O que Tauri cobre bem (reutilizar)

| Necessidade AstroCitizen Desktop | Tauri motorsport |
|----------------------------------|------------------|
| Auth Bearer + device/workspace | ? J� existe padr�o `/api/client/v1` |
| Fila offline + SQLite | ? `rusqlite` + sync queue |
| Upload de artefatos grandes | ? multipart + retry |
| Tray / app sempre ligada | ? |
| Linux + Windows | ? Tauri 2 |
| UI React partilh�vel com web | ? (componentes/design system) |
| Pull de ProgramaDiario | ? HTTP client Rust |

### 4.2 O que Tauri **n�o** resolve sozinho

| Necessidade | Por qu� |
|-------------|---------|
| **Alpyca / Alpaca** | Cliente Python oficial; ecossistema ASCOM |
| **udrv SBIG** | Binding ctypes j� no sbig-suite (Python) |
| **Astropy** (efem�rides locais, FITS headers, WCS) | Stack Python cient�fica |
| Console de sess�o em tempo real | Preview FITS, cooler, slew � hoje natural em PySide6 / Qt |
| Simuladores Omni + testes de dom�nio | J� planeados em Python (AC-040�) |

### 4.3 Op��es de arquitetura Desktop

| Op��o | Descri��o | Recomenda��o |
|-------|-----------|--------------|
| **A � Tauri-only** | Todo hardware em Rust | ? Reescrever udrv/Alpyca/Astropy � custo alto, risco |
| **B � PySide6-only** | Desktop como sbig-suite | ?? Perde sync/offline/tray j� maturados no Tauri |
| **C — Tauri + sidecar Python** | Tauri = shell + sync; Python sidecar | ❌ Substituído por D-009.4-rev (PySide6) |
| **D � Dois apps** | Tauri �agente sync� + PySide �console observat�rio� | ? Vi�vel; UX mais fragmentada |

**Decis�o proposta (C):**

```text
????????????????????????????????????????????????????????????
?  AstroCitizen Desktop (Tauri 2)                          ?
?  React UI � auth � sync queue � tray � settings          ?
?         ? IPC / local HTTP                               ?
?         ?                                                ?
?  observatory-runtime (Python)                            ?
?  CameraPort � MountPort � FocuserPort � Sess�o � FITS    ?
?  Alpyca � udrv � Astropy � simuladores                   ?
????????????????????????????????????????????????????????????
                        ? Sync API
                        ?
                 AstroCitizen SaaS
```

Analogia motorsport: Tauri = sync de ficheiros; Python cient�fico = an�lise.  
No AstroCitizen: Tauri = sync + shell; Python = **aquisi��o e hardware** (em vez de s� p�s-processamento).

---

## 5. Stack SaaS proposta (alinhada ao motorsport)

| Camada | Stack | Notas |
|--------|-------|-------|
| API | FastAPI + Pydantic v2 + SQLAlchemy 2 + Alembic | Igual motorsport |
| Web | Next.js + React + TypeScript + Tailwind | Igual motorsport |
| Auth | JWT (cookie web + Bearer Desktop) | Espelhar `/api/client/v1` |
| Workers | Jobs FastAPI / fila (redu��o, export) | Evolu��o Celery/RQ se necess�rio |
| Dom�nio cient�fico | Python + Astropy + Astroquery | Pacote partilhado `domain` |

---

## 6. Bancos: estruturado, semi-estruturado, n�o estruturado + BDaaS

### 6.1 Taxonomia de dados AstroCitizen

| Tipo | Exemplos | Forma |
|------|----------|-------|
| **Estruturado** | Site, Programa, Sessao, Observacao (metadados), estados RN-*, ContribuicaoRede | Relacional |
| **Semi-estruturado** | Snapshots meteo/efem�rides, headers FITS resumidos, planos di�rios JSON, produtos (curva pontos), configs PO-* | JSON / JSONB / Parquet |
| **N�o estruturado** | FITS brutos, masters, plots PNG, PDF, exports AAVSO bin�rios | Object / blob |
| **S�ries tabulares** | Pontos de curva de luz, amostras de espectro 1D, timings IOTA | Colunar (Parquet) ou tabelas particionadas |

### 6.2 Stack de persist�ncia (alvo)

| Store | Tecnologia | Modo | BDaaS? |
|-------|------------|------|--------|
| **BD operacional / cient�fico (mestre)** | **PostgreSQL 16+** | SaaS | **Sim** (Azure Flexible Server, AWS RDS, Neon, Supabase, etc.) |
| **Documentos flex�veis / eventos** | **JSONB no PostgreSQL** (1�) | SaaS | Inclu�do no Postgres DBaaS |
| **Document DB dedicado** (opcional P3) | MongoDB Atlas **ou** Cosmos DB | SaaS | **Sim**, s� se JSONB n�o bastar |
| **Object storage** | **S3-compatible** (AWS S3, Azure Blob, MinIO gerido, Cloudflare R2) | SaaS | **Sim** (storage-as-a-service) |
| **S�ries / an�lise** | **Parquet** no object store (+ cat�logo no Postgres) | SaaS | Object store BDaaS |
| **Cache / fila** (opcional) | Redis | SaaS | **Sim** (Azure Cache / ElastiCache) � P2+ |
| **Edge Desktop** | **SQLite** + filesystem local | Desktop | **N�o** (local; sync ? BDaaS) |

### 6.3 Princ�pio BDaaS

1. Em **produ��o SaaS**, nenhum estado mestre em disco da VM de aplica��o.  
2. `DATABASE_URL` ? Postgres gerido (SSL, backup, PITR) � mesmo padr�o do motorsport [Migra��o DBaaS].  
3. `ARTIFACT_STORE_URL` ? bucket gerido; BD s� guarda `uri` + hash + metadados (RN-110�116).  
4. CI continua com **SQLite in-memory** / Postgres de teste � sem custo BDaaS no pipeline.  
5. Desktop **nunca** � BDaaS: SQLite + upload; ap�s sync, a verdade est� no Postgres + object store.

### 6.4 Onde fica cada entidade

| Entidade / artefato | Store |
|---------------------|-------|
| Workspace, Site, Equipamento, Programa PO-* | Postgres |
| ProgramaDiario, Bloco, Sessao (metadados) | Postgres |
| Snapshot meteo / efem�rides | Postgres **JSONB** |
| Observacao (linha + headers_summary) | Postgres (+ JSONB) |
| FITS / masters / plots | Object storage |
| ProdutoAnalise (metadados + vers�o) | Postgres |
| Pontos curva de luz / espectro 1D | Parquet no object store **ou** tabelas Postgres (come�ar Postgres; migrar Parquet se volume) |
| ContribuicaoRede | Postgres |
| sync_queue (Desktop) | SQLite local |

### 6.5 Por que n�o Mongo como default

- Motorsport j� opera com **Postgres + JSON** e filesystem.  
- Um �nico DBaaS relacional com **JSONB** cobre semi-estruturado sem segundo motor no MVP.  
- Object store cobre n�o estruturado.  
- Avaliar Mongo/Cosmos s� se surgirem documentos com schema altamente vari�vel e queries document-first (ex.: atlas cient�fico enorme).

---

## 7. Decis�es (D-009)

| # | Decis�o |
|---|---------|
| D-009.1 | **SaaS** usa o mesmo stack de plataforma do motorsport: FastAPI + Next.js + SQLAlchemy/Alembic + PostgreSQL. |
| D-009.2 | **Produ��o:** PostgreSQL e object storage como **BDaaS**; Redis BDaaS se houver fila. |
| D-009.3 | Semi-estruturado: **JSONB no Postgres**; s�ries pesadas: **Parquet** em object storage (faseada). |
| D-009.4 | **Desktop:** Tauri 2 (padr�o client-motorsport) para shell/sync/auth/offline. |
| D-009.5 | **Observatory runtime:** processo/sidecar **Python** (Alpyca, udrv, Astropy) � n�o reimplementar em Rust. |
| D-009.6 | Dom�nio astron�mico partilhado em pacote Python (`domain` / ports), consumido por API e sidecar. |
| D-009.7 | API Desktop espelha contrato motorsport: `/api/client/v1/*` + Sync batch (ver API_ALVO.md). |

---

## 8. O que **n�o** copiar cegamente

| Motorsport | AstroCitizen |
|------------|--------------|
| Storage s� em disco da VM | Preferir object store BDaaS desde o in�cio |
| Watch de telemetria de jogos | Watch de FITS + eventos de sess�o do runtime Python |
| Pipeline p�s-upload como �nico Python | Python tamb�m no **edge** (aquisi��o) |
| Dom�nio ACC/iRacing | Dom�nio PO-*, RN-*, Astropy |
| PySide ausente | Sidecar pode expor UI Qt embutida **ou** s� API local + UI React no Tauri |

---

## 9. Implica��es no monorepo AstroCitizen

```text
astrocitizen/
??? packages/domain/           # Python � entidades, RN-*
??? packages/ports/
??? apps/saas-api/             # FastAPI (como motorsport-api)
??? apps/saas-web/             # Next.js (como motorsport-dashboard)
??? apps/desktop/              # Tauri 2 (como tauri-client)
??? apps/observatory-runtime/  # Python � hardware + sess�o (NOVO vs motorsport)
??? docs/
```

Fases sugeridas (alinhadas a F1�F6 de ARQUITETURA_SAAS_DESKTOP):

1. Skeleton SaaS API + Postgres DBaaS (ou Docker local com contrato DBaaS)  
2. Next.js workspace m�nimo  
3. Tauri sync shell (sem hardware)  
4. Sidecar Python + CameraPort sim/udrv  
5. Object storage BDaaS + sync artefatos  
6. An�lise/export no SaaS  

---

## 10. Crit�rios de aceite da decis�o

1. Documenta��o STACK e PERSISTENCIA atualizadas com BDaaS e taxonomia de dados.  
2. Desktop especificado como **Tauri + Python sidecar**, n�o PySide monol�tico.  
3. Nenhum requisito de �Mongo obrigat�rio� no MVP.  
4. TEST-HW-* continuam a validar udrv/Alpaca via runtime Python.  

---

## 11. Hist�rico

| Vers�o | Data | Notas |
|--------|------|-------|
| 1.0 | 2026-07-21 | Avalia��o motorsport ? AstroCitizen; D-009 |


---

## Addendum — D-009.4-rev (Desktop)

A opção **C (Tauri + sidecar)** desta avaliação foi **substituída** por:

- Desktop = **PySide6 monolítico** (UI + hardware + sync)
- Critério: [D-010](decisoes/D-010-otimizacao-recursos.md) + [COMPARACAO_DESKTOP_TAURI_VS_PYSIDE.md](COMPARACAO_DESKTOP_TAURI_VS_PYSIDE.md)
- DoD: `.exe` Windows (AC-075/076)

SaaS (FastAPI + Next.js + BDaaS) permanece conforme D-009.1–3.
