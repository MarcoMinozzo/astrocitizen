# Modelo de dados v1 — AstroCitizen

**Versão:** 1.0  
**Data:** 2026-07-21  
**Status:** especificação (pré-implementação) · alvo **AC-010**  
**Motor SaaS:** PostgreSQL 16+ (BDaaS)  
**Motor Desktop:** SQLite (espelho + fila sync)  
**Relacionados:** [PERSISTENCIA_E_BANCOS.md](PERSISTENCIA_E_BANCOS.md) · [MODELO_DE_SINCRONIZACAO.md](MODELO_DE_SINCRONIZACAO.md) · [API_ALVO.md](API_ALVO.md) · RN-110…116 · D-009 · D-010

---

## 1. Objectivo

Definir o **schema relacional v1** suficiente para:

1. Workspace multi-site  
2. Inventário + programas PO-*  
3. Programa diário + sessão + observações  
4. Produtos de análise + contribuição rede  
5. Sync Desktop ? SaaS com idempotência  

Fora de v1: warehouse, OpenSearch, Mongo dedicado, TimescaleDB.

---

## 2. Convenções

| Regra | Detalhe |
|-------|---------|
| PK | `UUID` (`gen_random_uuid()` no PG; texto UUID no SQLite) |
| Tempo | Timestamps **UTC** (`timestamptz` no PG) |
| Soft-delete | `deleted_at timestamptz NULL` — RN-114 |
| Optimistic lock | `version INTEGER NOT NULL DEFAULT 1` — sync / API |
| Tenant | Quase todas as tabelas de negócio: `workspace_id` |
| JSON | `JSONB` no PG · `TEXT` JSON no SQLite |
| Dinheiro/credenciais | **Nunca** em claro; secrets fora do BD de resultados |
| Nomes | `snake_case`; tabelas no plural |
| Migrações | Alembic no SaaS; Desktop aplica subset + `schema_migrations` |

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

## 3. Diagrama lógico (resumo)

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
| locale | TEXT | default `pt-BR` |
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

## 5. Inventário e local

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
| night_start_rule | TEXT | `astronomical_twilight` \| … |
| meteo_thresholds | JSONB | ver §11 |
| horizon_mask | JSONB NULL | opcional |
| is_default | BOOLEAN | |

**Índices:** `(workspace_id, name)`; `(workspace_id) WHERE deleted_at IS NULL`.

### 5.2 `equipment`

| Coluna | Tipo | Notas |
|--------|------|-------|
| id | UUID PK | |
| workspace_id | UUID | |
| type | TEXT | `camera` \| `mount` \| `focuser` \| `filter_wheel` \| `spectrograph` \| … |
| name | TEXT | |
| backend | TEXT NULL | `udrv` \| `alpaca` \| `sim` |
| available | BOOLEAN | RN-035 |
| metadata | JSONB | serial, modelo, host Alpaca… |

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
| role | TEXT | `camera` \| `mount` \| `focuser` \| … |
| UNIQUE(config_id, role) | | |

### 5.5 `targets`

| Coluna | Tipo | Notas |
|--------|------|-------|
| id | UUID PK | |
| workspace_id | UUID | |
| designation | TEXT | |
| ra_deg | DOUBLE NULL | |
| dec_deg | DOUBLE NULL | |
| target_type | TEXT | `star` \| `neo` \| `sn` \| `field` \| … |
| external_ids | JSONB | `{ "simbad": "…", "aavso": "…" }` |

**Índices:** `(workspace_id, designation)`; GIN em `external_ids` (PG).

---

## 6. Programas observacionais

### 6.1 `program_templates` (catálogo PO-* — seed)

| Coluna | Tipo | Notas |
|--------|------|-------|
| id | TEXT PK | `PO-A01` |
| class | TEXT | A–K |
| name | TEXT | |
| technique | TEXT | |
| default_networks | JSONB | `["AAVSO"]` |
| minimum_product | TEXT | |
| metadata | JSONB | |

Só leitura na app; atualizado com o catálogo oficial.

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
| cadence | JSONB | regras de cadência |
| settings | JSONB | limiares específicos |

**Índices:** `(workspace_id, state)`; `(workspace_id, priority)`.

### 6.3 `program_targets`

| Coluna | Tipo | Notas |
|--------|------|-------|
| program_id | UUID | |
| target_id | UUID | |
| role | TEXT | `primary` \| `comp` \| `check` |
| sort_order | INTEGER | |

---

## 7. Planejamento diário

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

**Índices:** `(daily_plan_id, sort_order)`; `(daily_plan_id, status)`.

---

## 8. Sessão e observação

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
| plan_snapshot | JSONB | cópia imutável do plano |
| meteo_start_id | UUID NULL | |
| meteo_end_id | UUID NULL | |
| client_id | UUID NULL | id local Desktop (idempotência) |

### 8.2 `session_events`

| Coluna | Tipo | Notas |
|--------|------|-------|
| id | UUID PK | |
| session_id | UUID | |
| block_id | UUID NULL | |
| event_type | TEXT | `block.started` \| `block.completed` \| … |
| occurred_at_utc | TIMESTAMPTZ | |
| payload | JSONB | |
| client_op_id | UUID NULL | UNIQUE parcial — sync |

### 8.3 `observations`

| Coluna | Tipo | Notas |
|--------|------|-------|
| id | UUID PK | |
| workspace_id | UUID | |
| client_id | UUID NULL | UNIQUE(workspace_id, client_id) — sync |
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
| headers_summary | JSONB | EXPTIME, FILTER, … |
| notes | TEXT | |

**Índices:**  
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
| kind | TEXT | `fits_raw` \| `fits_reduced` \| `plot` \| `export` \| `parquet` \| … |
| uri | TEXT | object store ou path relativo Desktop |
| filename | TEXT | |
| sha256 | TEXT | |
| size_bytes | BIGINT | |
| content_type | TEXT | |
| immutable | BOOLEAN | true para bruto (RN-111) |
| upload_status | TEXT | `pending` \| `uploaded` \| `failed` |

**Índices:** `(observation_id)`; `(sha256)`; `(workspace_id, kind)`.

---

## 9. Análise e contribuição

### 9.1 `analysis_products`

| Coluna | Tipo | Notas |
|--------|------|-------|
| id | UUID PK | |
| workspace_id | UUID | |
| program_id | UUID NULL | |
| product_type | TEXT | `light_curve` \| `spectrum_1d` \| `astrometry` \| `timing` \| … |
| version_num | INTEGER | RN-072 |
| parent_product_id | UUID NULL | versão anterior |
| is_publishable | BOOLEAN | |
| parameters | JSONB | params de redução |
| summary | JSONB | stats, ? range, … |
| state | TEXT | `draft` \| `ready` \| `superseded` |

**Relação N:N com observações:** `analysis_product_observations(product_id, observation_id)`.

### 9.2 `measurement_points` (MVP — séries no Postgres)

| Coluna | Tipo | Notas |
|--------|------|-------|
| id | BIGSERIAL / UUID | |
| product_id | UUID | |
| t_utc | TIMESTAMPTZ NULL | ou `sequence_index` |
| sequence_index | INTEGER NULL | espectro |
| x | DOUBLE | tempo, ?, … |
| y | DOUBLE | fluxo, mag, … |
| y_err | DOUBLE NULL | |
| band | TEXT NULL | |
| meta | JSONB NULL | |

**Índices:** `(product_id, sequence_index)`; `(product_id, t_utc)`.

**Promoção a Parquet (§12):** quando critérios forem atingidos, gravar artefacto `kind=parquet` e opcionalmente arquivar pontos (manter amostra ou só summary no BD).

### 9.3 `network_contributions`

| Coluna | Tipo | Notas |
|--------|------|-------|
| id | UUID PK | |
| workspace_id | UUID | |
| program_id | UUID | |
| product_id | UUID | |
| network | TEXT | `AAVSO` \| `MPC` \| `IOTA` \| `ARAS` \| … |
| state | TEXT | RN-081 |
| payload_preview | JSONB | campos atlas |
| artifact_id | UUID NULL | ficheiro export |
| external_ref | TEXT NULL | id na rede |
| error_message | TEXT NULL | |

**Índices:** `(workspace_id, network, state)`; `(program_id)`.

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
| payload | JSONB | nuvens, vento, humidade, … RN-113 |

### 10.2 `ephemeris_snapshots`

| Coluna | Tipo | Notas |
|--------|------|-------|
| id | UUID PK | |
| workspace_id | UUID | |
| site_id | UUID | |
| target_id | UUID NULL | |
| epoch_utc | TIMESTAMPTZ | |
| source | TEXT | `astropy` \| `horizons` \| `cache` |
| payload | JSONB | alt, az, airmass, events… |

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

**Índice:** `(workspace_id, at_utc DESC)`.

---

## 11. Formas JSONB (contratos mínimos)

### `sites.meteo_thresholds`

```json
{
  "max_cloud_cover_pct": 50,
  "max_wind_ms": 12,
  "max_humidity_pct": 90,
  "no_precipitation": true
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

Cópia do `daily_plan` + `observation_blocks` no instante do start (RN-056). Schema versionado: `{"schema": 1, "plan": {...}, "blocks": [...]}`.

### `programs.cadence`

```json
{
  "min_interval_hours": 24,
  "preferred_filters": ["V", "B"],
  "max_airmass": 2.0
}
```

---

## 12. Critério Postgres ? Parquet (séries)

Promover `measurement_points` ? artefacto Parquet quando **qualquer** condição:

| Métrica | Limiar v1 (ajustável) |
|---------|------------------------|
| Pontos por produto | > 50_000 |
| Tamanho estimado | > 10 MB |
| Tipo de produto | espectro high-res / timing alta cadência (flag no template) |

Após promoção:

1. Criar `artifacts` com `kind=parquet`, `uri` no object store.  
2. `analysis_products.summary` guarda estatísticas + `parquet_artifact_id`.  
3. Pontos tabulares: soft-delete em lote ou tabela archive (job).  
4. Leitura analítica: pandas/polars a partir do Parquet.

Alinhado a D-010 (não manter séries enormes em linha relacional sem necessidade).

---

## 13. Desktop SQLite — diferenças

| Aspeto | SaaS (PG) | Desktop (SQLite) |
|--------|-----------|------------------|
| JSON | JSONB | TEXT JSON |
| UUID | nativo | TEXT |
| Espelho | mestre | subset: sites, equipment, programs, daily_plans, blocks, sessions, observations, artifacts locais |
| Extra | — | `sync_queue`, `sync_cursor`, `local_artifacts`, `entity_versions` (ver MODELO_DE_SINCRONIZACAO) |
| Object store | S3 URI | `file://` ou path relativo até upload |
| Migrações | Alembic | `schema_migrations` + scripts alinhados à versão de protocolo sync |

**Regra:** tipos lógicos iguais; adapters SQLAlchemy com dialect checks (padrão motorsport).

---

## 14. Consultas típicas (índices cobrem)

| Caso de uso | Filtro principal |
|-------------|------------------|
| Arquivo por noite | `observations.observed_at_utc` + `site_id` |
| Gestão multi-programa | `programs.state` + `observations.program_id` |
| Export pendente | `network_contributions.state` |
| Excluir simuladas | `observations.simulated = false` |
| Sessão activa | `sessions.state = 'active'` |
| Plano da noite | `daily_plans (site_id, night_date)` |

---

## 15. Mapa entidade de domínio ? tabela

| Domínio | Tabela |
|---------|--------|
| Site | `sites` |
| Equipamento | `equipment` |
| ConfiguraçãoInstrumental | `instrument_configs` (+ items) |
| Alvo | `targets` |
| ProgramaObservacional | `programs` |
| Template PO-* | `program_templates` |
| ProgramaDiario | `daily_plans` |
| BlocoObservacional | `observation_blocks` |
| Sessao | `sessions` |
| Observacao | `observations` |
| ProdutoAnalise | `analysis_products` |
| ContribuicaoRede | `network_contributions` |
| CondiçãoMeteo | `meteo_snapshots` |
| Efeméride (snapshot) | `ephemeris_snapshots` |

---

## 16. Implementação (backlog)

| ID | Item |
|----|------|
| AC-010 | `ArchivePort` + este modelo relacional v1 |
| AC-011 | Adapter SQLite Desktop + migrações |
| AC-011b | Adapter PostgreSQL SaaS + Alembic |
| AC-012 | `ArtifactStorePort` (URI + sha256) |
| AC-013 | Soft-delete + `audit_log` |
| AC-014 | Flag `simulated` + filtros |

Seed: carregar `program_templates` a partir de `PROGRAMAS_OBSERVACIONAIS.md` (YAML/JSON gerado).

---

## 17. Explicitamente adiado (pós-v1)

- OpenSearch / FTS avançado em documentação  
- PostGIS (horizonte complexo)  
- TimescaleDB / hypertables  
- Mongo/Cosmos  
- Particionamento nativo de `observations` por mês (reavaliar >1M linhas)  
- Vector DB para RAG em docs  

---

## 18. Critérios de aceite do modelo v1

1. Cobre entidades do escopo §4 e RN-110…116.  
2. Suporta sync idempotente (`client_id` / `client_op_id`).  
3. Soft-delete + `version` em entidades mutáveis syncáveis.  
4. FITS só como `artifacts.uri`, nunca BLOB no PG.  
5. Séries MVP em `measurement_points` com limiar Parquet documentado.  
6. Um `workspace_id` isola dados de gestão (RN futuro multi-user).

---

## 19. Histórico

| Versão | Data | Notas |
|--------|------|-------|
| 1.0 | 2026-07-21 | Schema lógico v1 completo para S1–S5 |
