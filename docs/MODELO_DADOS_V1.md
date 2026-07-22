# Modelo de dados v1 ù AstroCitizen

**Versùo:** 1.0  
**Data:** 2026-07-21  
**Status:** especificaùùo (prù-implementaùùo) ù alvo **AC-010**  
**Motor SaaS:** PostgreSQL 16+ (BDaaS)  
**Motor Desktop:** SQLite (espelho + fila sync)  
**Relacionados:** [PERSISTENCIA_E_BANCOS.md](PERSISTENCIA_E_BANCOS.md) ù [MODELO_DE_SINCRONIZACAO.md](MODELO_DE_SINCRONIZACAO.md) ù [API_ALVO.md](API_ALVO.md) ù RN-110ù116 ù D-009 ù D-010

---

## 1. Objectivo

Definir o **schema relacional v1** suficiente para:

1. Workspace multi-site  
2. Inventùrio + programas PO-*  
3. Programa diùrio + sessùo + observaùùes  
4. Produtos de anùlise + contribuiùùo rede  
5. Sync Desktop ? SaaS com idempotùncia  

Fora de v1: warehouse, OpenSearch, Mongo dedicado, TimescaleDB.

---

## 2. Convenùùes

| Regra | Detalhe |
|-------|---------|
| PK | `UUID` (`gen_random_uuid()` no PG; texto UUID no SQLite) |
| Tempo | Timestamps **UTC** (`timestamptz` no PG) |
| Soft-delete | `deleted_at timestamptz NULL` ù RN-114 |
| Optimistic lock | `version INTEGER NOT NULL DEFAULT 1` ù sync / API |
| Tenant | Quase todas as tabelas de negùcio: `workspace_id` |
| JSON | `JSONB` no PG ù `TEXT` JSON no SQLite |
| Dinheiro/credenciais | **Nunca** em claro; secrets fora do BD de resultados |
| Nomes | `snake_case`; tabelas no plural |
| Migraùùes | Alembic no SaaS; Desktop aplica subset + `schema_migrations` |

### Colunas transversais (quase todas as tabelas)

```text
id              UUID PK
workspace_id    UUID NOT NULL  ? workspaces(id)   [exceto users/workspaces]
created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
deleted_at      TIMESTAMPTZ NULL
version         INTEGER NOT NULL DEFAULT 1
```

---

## 3. Diagrama lùgico (resumo)

```text
users ??< workspaces >?? workspace_members
                ?
                ??? sites
                ??? equipment ??< instrument_configs >?? instrument_config_items
                ??? targets
                ??? programs (PO-*) ??< program_targets
                ??? daily_plans ??< observation_blocks
                ??? sessions ??< session_events
                ??? observations ??< artifacts
                ??? analysis_products ??< measurement_points (MVP)
                ??? network_contributions
                ??? meteo_snapshots / ephemeris_snapshots
                ??? audit_log
```

---

## 4. Identidade e workspace

### 4.1 `users`

| Coluna | Tipo | Notas |
|--------|------|-------|
| id | UUID PK | |
| email | CITEXT UNIQUE | |
| password_hash | TEXT | ou auth externo |
| display_name | TEXT | |
| locale | TEXT | preferencia UI: `auto` \| `pt` \| `es` \| `en` (RN-120); default efectivo via deteccao SO/browser, fallback `en` |
| created_at / updated_at / deleted_at | | |

### 4.2 `workspaces`

| Coluna | Tipo | Notas |
|--------|------|-------|
| id | UUID PK | |
| name | TEXT | |
| owner_user_id | UUID ? users | |
| created_at / updated_at / deleted_at / version | | |

### 4.3 `workspace_members`

| Coluna | Tipo | Notas |
|--------|------|-------|
| workspace_id | UUID | PK composta |
| user_id | UUID | PK composta |
| role | TEXT | `owner` \| `member` \| `viewer` |

### 4.4 `devices` (Desktop)

| Coluna | Tipo | Notas |
|--------|------|-------|
| id | UUID PK | |
| workspace_id | UUID | |
| name | TEXT | |
| platform | TEXT | `linux` \| `windows` |
| token_hash | TEXT | device token |
| last_seen_at | TIMESTAMPTZ | |
| revoked_at | TIMESTAMPTZ NULL | |

---

## 5. Inventùrio e local

### 5.1 `sites`

| Coluna | Tipo | Notas |
|--------|------|-------|
| id | UUID PK | |
| workspace_id | UUID | |
| name | TEXT | |
| latitude_deg | DOUBLE | |
| longitude_deg | DOUBLE | |
| elevation_m | DOUBLE | |
| timezone | TEXT | IANA |
| min_altitude_deg | DOUBLE | default 25 |
| night_start_rule | TEXT | `astronomical_twilight` \| ù |
| meteo_thresholds | JSONB | ver ù11 |
| horizon_mask | JSONB NULL | opcional |
| is_default | BOOLEAN | |

**ùndices:** `(workspace_id, name)`; `(workspace_id) WHERE deleted_at IS NULL`.

### 5.2 `equipment`

| Coluna | Tipo | Notas |
|--------|------|-------|
| id | UUID PK | |
| workspace_id | UUID | |
| type | TEXT | `camera` \| `mount` \| `focuser` \| `filter_wheel` \| `spectrograph` \| ù |
| name | TEXT | |
| backend | TEXT NULL | `udrv` \| `alpaca` \| `sim` |
| available | BOOLEAN | RN-035 |
| metadata | JSONB | serial, modelo, host Alpacaù |

### 5.3 `instrument_configs`

| Coluna | Tipo | Notas |
|--------|------|-------|
| id | UUID PK | |
| workspace_id | UUID | |
| name | TEXT | preset |
| notes | TEXT | |

### 5.4 `instrument_config_items`

| Coluna | Tipo | Notas |
|--------|------|-------|
| config_id | UUID ? instrument_configs | |
| equipment_id | UUID ? equipment | |
| role | TEXT | `camera` \| `mount` \| `focuser` \| ù |
| UNIQUE(config_id, role) | | |

### 5.5 `targets`

| Coluna | Tipo | Notas |
|--------|------|-------|
| id | UUID PK | |
| workspace_id | UUID | |
| designation | TEXT | |
| ra_deg | DOUBLE NULL | |
| dec_deg | DOUBLE NULL | |
| target_type | TEXT | `star` \| `neo` \| `sn` \| `field` \| ù |
| external_ids | JSONB | `{ "simbad": "ù", "aavso": "ù" }` |

**ùndices:** `(workspace_id, designation)`; GIN em `external_ids` (PG).

---

## 6. Programas observacionais

### 6.1 `program_templates` (catùlogo PO-* ù seed)

| Coluna | Tipo | Notas |
|--------|------|-------|
| id | TEXT PK | `PO-A01` |
| class | TEXT | AùK |
| name | TEXT | |
| technique | TEXT | |
| default_networks | JSONB | `["AAVSO"]` |
| minimum_product | TEXT | |
| metadata | JSONB | |

Sù leitura na app; atualizado com o catùlogo oficial.

### 6.2 `programs`

| Coluna | Tipo | Notas |
|--------|------|-------|
| id | UUID PK | |
| workspace_id | UUID | |
| template_id | TEXT ? program_templates | RN-046 |
| name | TEXT | |
| state | TEXT | `draft` \| `active` \| `paused` \| `archived` |
| priority | INTEGER | RN-042 |
| default_instrument_config_id | UUID NULL | |
| export_networks | JSONB | |
| minimum_product | TEXT | RN-043 |
| cadence | JSONB | regras de cadùncia |
| settings | JSONB | limiares especùficos |

**ùndices:** `(workspace_id, state)`; `(workspace_id, priority)`.

### 6.3 `program_targets`

| Coluna | Tipo | Notas |
|--------|------|-------|
| program_id | UUID | |
| target_id | UUID | |
| role | TEXT | `primary` \| `comp` \| `check` |
| sort_order | INTEGER | |

---

## 7. Planejamento diùrio

### 7.1 `daily_plans`

| Coluna | Tipo | Notas |
|--------|------|-------|
| id | UUID PK | |
| workspace_id | UUID | |
| site_id | UUID | |
| night_date | DATE | noite civil do site (RN-004) |
| state | TEXT | `draft` \| `published` \| `in_execution` \| `closed` |
| generated_at | TIMESTAMPTZ | |
| published_at | TIMESTAMPTZ NULL | |
| UNIQUE(workspace_id, site_id, night_date) WHERE deleted_at IS NULL | | RN-050 |

### 7.2 `observation_blocks`

| Coluna | Tipo | Notas |
|--------|------|-------|
| id | UUID PK | |
| daily_plan_id | UUID | |
| program_id | UUID NULL | |
| target_id | UUID NULL | |
| instrument_config_id | UUID NULL | |
| sort_order | INTEGER | |
| window_start_utc | TIMESTAMPTZ | |
| window_end_utc | TIMESTAMPTZ | |
| predicted_altitude_deg | DOUBLE NULL | |
| airmass | DOUBLE NULL | |
| status | TEXT | RN-053 |
| status_reason | TEXT NULL | RN-054 |
| priority | INTEGER | |
| notes | TEXT | |
| ephemeris_snapshot_id | UUID NULL | |
| meteo_snapshot_id | UUID NULL | |
| technique | TEXT NULL | |

**ùndices:** `(daily_plan_id, sort_order)`; `(daily_plan_id, status)`.

---

## 8. Sessùo e observaùùo

### 8.1 `sessions`

| Coluna | Tipo | Notas |
|--------|------|-------|
| id | UUID PK | |
| workspace_id | UUID | |
| site_id | UUID | |
| daily_plan_id | UUID | |
| daily_plan_version | INTEGER | RN-056 |
| device_id | UUID NULL | |
| started_at_utc | TIMESTAMPTZ | |
| ended_at_utc | TIMESTAMPTZ NULL | |
| state | TEXT | `active` \| `ended` \| `aborted` |
| plan_snapshot | JSONB | cùpia imutùvel do plano |
| meteo_start_id | UUID NULL | |
| meteo_end_id | UUID NULL | |
| client_id | UUID NULL | id local Desktop (idempotùncia) |

### 8.2 `session_events`

| Coluna | Tipo | Notas |
|--------|------|-------|
| id | UUID PK | |
| session_id | UUID | |
| block_id | UUID NULL | |
| event_type | TEXT | `block.started` \| `block.completed` \| ù |
| occurred_at_utc | TIMESTAMPTZ | |
| payload | JSONB | |
| client_op_id | UUID NULL | UNIQUE parcial ù sync |

### 8.3 `observations`

| Coluna | Tipo | Notas |
|--------|------|-------|
| id | UUID PK | |
| workspace_id | UUID | |
| client_id | UUID NULL | UNIQUE(workspace_id, client_id) ù sync |
| session_id | UUID NULL | |
| site_id | UUID | |
| block_id | UUID NULL | |
| program_id | UUID NULL | |
| target_id | UUID NULL | |
| instrument_config_id | UUID NULL | |
| observed_at_utc | TIMESTAMPTZ | |
| state | TEXT | `raw` \| `calibrated` \| `analyzed` \| `publishable` \| `archived` |
| camera_backend | TEXT | `udrv` \| `alpaca` \| `sim` |
| simulated | BOOLEAN | RN-115 |
| meteo_manual | BOOLEAN | RN-023 |
| meteo_snapshot_id | UUID NULL | |
| headers_summary | JSONB | EXPTIME, FILTER, ù |
| notes | TEXT | |

**ùndices:**  
`(workspace_id, observed_at_utc DESC)`;  
`(workspace_id, program_id, observed_at_utc)`;  
`(workspace_id, target_id)`;  
`(workspace_id, simulated)`;  
`(session_id)`.

### 8.4 `artifacts`

| Coluna | Tipo | Notas |
|--------|------|-------|
| id | UUID PK | |
| workspace_id | UUID | |
| observation_id | UUID NULL | |
| product_id | UUID NULL | ? analysis_products |
| kind | TEXT | `fits_raw` \| `fits_reduced` \| `plot` \| `export` \| `parquet` \| ù |
| uri | TEXT | object store ou path relativo Desktop |
| filename | TEXT | |
| sha256 | TEXT | |
| size_bytes | BIGINT | |
| content_type | TEXT | |
| immutable | BOOLEAN | true para bruto (RN-111) |
| upload_status | TEXT | `pending` \| `uploaded` \| `failed` |

**ùndices:** `(observation_id)`; `(sha256)`; `(workspace_id, kind)`.

---

## 9. Anùlise e contribuiùùo

### 9.1 `analysis_products`

| Coluna | Tipo | Notas |
|--------|------|-------|
| id | UUID PK | |
| workspace_id | UUID | |
| program_id | UUID NULL | |
| product_type | TEXT | `light_curve` \| `spectrum_1d` \| `astrometry` \| `timing` \| ù |
| version_num | INTEGER | RN-072 |
| parent_product_id | UUID NULL | versùo anterior |
| is_publishable | BOOLEAN | |
| parameters | JSONB | params de reduùùo |
| summary | JSONB | stats, ? range, ù |
| state | TEXT | `draft` \| `ready` \| `superseded` |

**Relaùùo N:N com observaùùes:** `analysis_product_observations(product_id, observation_id)`.

### 9.2 `measurement_points` (MVP ù sùries no Postgres)

| Coluna | Tipo | Notas |
|--------|------|-------|
| id | BIGSERIAL / UUID | |
| product_id | UUID | |
| t_utc | TIMESTAMPTZ NULL | ou `sequence_index` |
| sequence_index | INTEGER NULL | espectro |
| x | DOUBLE | tempo, ?, ù |
| y | DOUBLE | fluxo, mag, ù |
| y_err | DOUBLE NULL | |
| band | TEXT NULL | |
| meta | JSONB NULL | |

**ùndices:** `(product_id, sequence_index)`; `(product_id, t_utc)`.

**Promoùùo a Parquet (ù12):** quando critùrios forem atingidos, gravar artefacto `kind=parquet` e opcionalmente arquivar pontos (manter amostra ou sù summary no BD).

### 9.3 `network_contributions`

| Coluna | Tipo | Notas |
|--------|------|-------|
| id | UUID PK | |
| workspace_id | UUID | |
| program_id | UUID | |
| product_id | UUID | |
| network | TEXT | `AAVSO` \| `MPC` \| `IOTA` \| `ARAS` \| ù |
| state | TEXT | RN-081 |
| payload_preview | JSONB | campos atlas |
| artifact_id | UUID NULL | ficheiro export |
| external_ref | TEXT NULL | id na rede |
| error_message | TEXT NULL | |

**ùndices:** `(workspace_id, network, state)`; `(program_id)`.

---

## 10. Snapshots e auditoria

### 10.1 `meteo_snapshots`

| Coluna | Tipo | Notas |
|--------|------|-------|
| id | UUID PK | |
| workspace_id | UUID | |
| site_id | UUID | |
| captured_at_utc | TIMESTAMPTZ | |
| source | TEXT | `api` \| `alpaca_oc` \| `manual` |
| payload | JSONB | nuvens, vento, humidade, ù RN-113 |

### 10.2 `ephemeris_snapshots`

| Coluna | Tipo | Notas |
|--------|------|-------|
| id | UUID PK | |
| workspace_id | UUID | |
| site_id | UUID | |
| target_id | UUID NULL | |
| epoch_utc | TIMESTAMPTZ | |
| source | TEXT | `astropy` \| `horizons` \| `cache` |
| payload | JSONB | alt, az, airmass, eventsù |

### 10.3 `audit_log`

| Coluna | Tipo | Notas |
|--------|------|-------|
| id | BIGSERIAL | |
| workspace_id | UUID NULL | |
| user_id | UUID NULL | |
| device_id | UUID NULL | |
| action | TEXT | |
| entity_type | TEXT | |
| entity_id | UUID NULL | |
| at_utc | TIMESTAMPTZ | |
| detail | JSONB | RN-100 |

**ùndice:** `(workspace_id, at_utc DESC)`.

---

## 11. Formas JSONB (contratos mùnimos)

### `sites.meteo_thresholds`

```json
{
  "max_cloud_cover_pct": 50,
  "max_wind_ms": 12,
  "max_humidity_pct": 90,
  "no_precipitation": true,
  "max_precip_probability_pct": 40,
  "min_dew_margin_c": 2.0
}
```

### `observations.headers_summary`

```json
{
  "EXPTIME": 60.0,
  "FILTER": "V",
  "BINNING": 1,
  "CCD-TEMP": -20.1,
  "IMAGETYP": "LIGHT"
}
```

### `sessions.plan_snapshot`

Cùpia do `daily_plan` + `observation_blocks` no instante do start (RN-056). Schema versionado: `{"schema": 1, "plan": {...}, "blocks": [...]}`.

### `programs.cadence`

```json
{
  "min_interval_hours": 24,
  "preferred_filters": ["V", "B"],
  "max_airmass": 2.0
}
```

---

## 12. Critùrio Postgres ? Parquet (sùries)

Promover `measurement_points` ? artefacto Parquet quando **qualquer** condiùùo:

| Mùtrica | Limiar v1 (ajustùvel) |
|---------|------------------------|
| Pontos por produto | > 50_000 |
| Tamanho estimado | > 10 MB |
| Tipo de produto | espectro high-res / timing alta cadùncia (flag no template) |

Apùs promoùùo:

1. Criar `artifacts` com `kind=parquet`, `uri` no object store.  
2. `analysis_products.summary` guarda estatùsticas + `parquet_artifact_id`.  
3. Pontos tabulares: soft-delete em lote ou tabela archive (job).  
4. Leitura analùtica: pandas/polars a partir do Parquet.

Alinhado a D-010 (nùo manter sùries enormes em linha relacional sem necessidade).

---

## 13. Desktop SQLite ù diferenùas

| Aspeto | SaaS (PG) | Desktop (SQLite) |
|--------|-----------|------------------|
| JSON | JSONB | TEXT JSON |
| UUID | nativo | TEXT |
| Espelho | mestre | subset: sites, equipment, programs, daily_plans, blocks, sessions, observations, artifacts locais |
| Extra | ù | `sync_queue`, `sync_cursor`, `local_artifacts`, `entity_versions` (ver MODELO_DE_SINCRONIZACAO) |
| Object store | S3 URI | `file://` ou path relativo atù upload |
| Migraùùes | Alembic | `schema_migrations` + scripts alinhados ù versùo de protocolo sync |

**Regra:** tipos lùgicos iguais; adapters SQLAlchemy com dialect checks (padrùo motorsport).

---

## 14. Consultas tùpicas (ùndices cobrem)

| Caso de uso | Filtro principal |
|-------------|------------------|
| Arquivo por noite | `observations.observed_at_utc` + `site_id` |
| Gestùo multi-programa | `programs.state` + `observations.program_id` |
| Export pendente | `network_contributions.state` |
| Excluir simuladas | `observations.simulated = false` |
| Sessùo activa | `sessions.state = 'active'` |
| Plano da noite | `daily_plans (site_id, night_date)` |

---

## 15. Mapa entidade de domùnio ? tabela

| Domùnio | Tabela |
|---------|--------|
| Site | `sites` |
| Equipamento | `equipment` |
| ConfiguraùùoInstrumental | `instrument_configs` (+ items) |
| Alvo | `targets` |
| ProgramaObservacional | `programs` |
| Template PO-* | `program_templates` |
| ProgramaDiario | `daily_plans` |
| BlocoObservacional | `observation_blocks` |
| Sessao | `sessions` |
| Observacao | `observations` |
| ProdutoAnalise | `analysis_products` |
| ContribuicaoRede | `network_contributions` |
| CondiùùoMeteo | `meteo_snapshots` |
| Efemùride (snapshot) | `ephemeris_snapshots` |

---

## 16. Implementaùùo (backlog)

| ID | Item |
|----|------|
| AC-010 | `ArchivePort` + este modelo relacional v1 |
| AC-011 | Adapter SQLite Desktop + migraùùes |
| AC-011b | Adapter PostgreSQL SaaS + Alembic |
| AC-012 | `ArtifactStorePort` (URI + sha256) |
| AC-013 | Soft-delete + `audit_log` |
| AC-014 | Flag `simulated` + filtros |

Seed: carregar `program_templates` a partir de `PROGRAMAS_OBSERVACIONAIS.md` (YAML/JSON gerado).

---

## 17. Explicitamente adiado (pùs-v1)

- OpenSearch / FTS avanùado em documentaùùo  
- PostGIS (horizonte complexo)  
- TimescaleDB / hypertables  
- Mongo/Cosmos  
- Particionamento nativo de `observations` por mùs (reavaliar >1M linhas)  
- Vector DB / embeddings para RAG ó agora planejado no epico **E19** ([EPICO_E19_BASE_CONHECIMENTO_RAG.md](EPICO_E19_BASE_CONHECIMENTO_RAG.md)); fora do schema observacional v1

---

## 18. Critùrios de aceite do modelo v1

1. Cobre entidades do escopo ù4 e RN-110ù116.  
2. Suporta sync idempotente (`client_id` / `client_op_id`).  
3. Soft-delete + `version` em entidades mutùveis syncùveis.  
4. FITS sù como `artifacts.uri`, nunca BLOB no PG.  
5. Sùries MVP em `measurement_points` com limiar Parquet documentado.  
6. Um `workspace_id` isola dados de gestùo (RN futuro multi-user).

---

## 19. Histùrico

| Versùo | Data | Notas |
|--------|------|-------|
| 1.0 | 2026-07-21 | Schema lùgico v1 completo para S1ùS5 |
