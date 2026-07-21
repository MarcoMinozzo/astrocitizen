# API alvo — AstroCitizen (SaaS ? Desktop)

**Versão:** 1.0  
**Data:** 2026-07-21  
**Status:** especificação de contratos  
**Base:** [ARQUITETURA_SAAS_DESKTOP.md](ARQUITETURA_SAAS_DESKTOP.md) · [WORKFLOWS.md](WORKFLOWS.md)

---

## 1. Propósito

Define os **contratos de serviço** entre:

- **Cliente Desktop** (edge, observatório)
- **Serviço SaaS** (cloud, fonte mestre)

Não cobre APIs públicas de redes cidadãs (AAVSO, MPC…) — ver [atlas/ATLAS_REPORTE_OBSERVACOES.md](atlas/ATLAS_REPORTE_OBSERVACOES.md).

Convenções:

- Base URL: `https://api.astrocitizen.example/v1`
- Formato: JSON (`application/json`)
- Identificadores: UUID v4
- Tempos: ISO 8601 UTC
- Paginação: `?cursor=` / `next_cursor` em listas longas

---

## 2. Autenticação

### 2.1 Login (usuário)

```http
POST /auth/token
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "..."
}
```

Resposta:

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "expires_in": 3600,
  "workspace_id": "uuid"
}
```

### 2.2 Dispositivo Desktop (recomendado)

Fluxo device code ou pairing:

```http
POST /auth/devices/register
Authorization: Bearer {user_access_token}

{
  "device_name": "Observatório Gramadão",
  "platform": "linux"
}
```

Resposta:

```json
{
  "device_id": "uuid",
  "device_token": "...",
  "expires_at": "2027-07-21T00:00:00Z"
}
```

Requisições subsequentes do Desktop:

```http
Authorization: Bearer {device_token}
X-Device-Id: {device_id}
X-Workspace-Id: {workspace_id}
```

---

## 3. Recursos e endpoints

### 3.1 Workspace

| Método | Path | Descrição |
|--------|------|-----------|
| GET | `/workspaces/me` | Workspace do usuário autenticado |
| GET | `/workspaces/{id}/sites` | Lista sites do workspace |

### 3.2 Sites (`GerirSite`)

| Método | Path | Descrição |
|--------|------|-----------|
| GET | `/sites/{id}` | Detalhe SiteProfile |
| POST | `/sites` | Criar site |
| PATCH | `/sites/{id}` | Atualizar site |
| GET | `/sites/{id}/thresholds` | Limiares meteo/altitude |

**SiteProfile (resposta):**

```json
{
  "id": "uuid",
  "workspace_id": "uuid",
  "name": "Gramadão",
  "latitude_deg": -29.95,
  "longitude_deg": -51.08,
  "elevation_m": 750.0,
  "timezone": "America/Sao_Paulo",
  "min_altitude_deg": 25.0,
  "night_start_rule": "astronomical_twilight",
  "updated_at": "2026-07-21T12:00:00Z",
  "version": 3
}
```

### 3.3 Equipamento (`GerirEquipamento`)

| Método | Path | Descrição |
|--------|------|-----------|
| GET | `/equipment` | Inventário do workspace |
| GET | `/equipment/{id}` | Item |
| POST | `/equipment` | Registrar |
| PATCH | `/equipment/{id}` | Atualizar (incl. `available`) |
| GET | `/instrument-configs` | Configurações instrumentais |
| POST | `/instrument-configs` | Criar preset |

**Equipamento:**

```json
{
  "id": "uuid",
  "type": "camera",
  "name": "ST-8XME",
  "backend": "udrv",
  "metadata": {},
  "available": true,
  "version": 1
}
```

### 3.4 Programas observacionais (`GerirProgramas`)

| Método | Path | Descrição |
|--------|------|-----------|
| GET | `/programs` | Lista (`?state=active`) |
| GET | `/programs/{id}` | Detalhe campanha |
| POST | `/programs` | Instanciar de template PO-* |
| PATCH | `/programs/{id}` | Atualizar / mudar estado |
| GET | `/program-templates` | Catálogo PO-* (metadados) |

**ProgramaObservacional:**

```json
{
  "id": "uuid",
  "template_id": "PO-A01",
  "name": "Variáveis AAVSO 2026",
  "state": "active",
  "priority": 10,
  "targets": [{"designation": "T UMi", "ra_deg": 0, "dec_deg": 0}],
  "default_instrument_config_id": "uuid",
  "export_networks": ["AAVSO"],
  "minimum_product": "differential_photometry_curve",
  "version": 5
}
```

### 3.5 Planejamento (`PlanejarDia`)

| Método | Path | Descrição |
|--------|------|-----------|
| POST | `/daily-plans/generate` | Gerar/atualizar para site + data |
| GET | `/daily-plans/{id}` | Plano completo com blocos |
| PATCH | `/daily-plans/{id}` | Edição manual (reordenar, remover) |
| POST | `/daily-plans/{id}/publish` | Publicar (`rascunho` ? `publicado`) |
| GET | `/daily-plans` | Lista (`?site_id=&night_date=`) |

**Gerar plano:**

```http
POST /daily-plans/generate
{
  "site_id": "uuid",
  "night_date": "2026-07-21",
  "force_refresh_ephemeris": true,
  "force_refresh_meteo": true
}
```

**BlocoObservacional (dentro do plano):**

```json
{
  "id": "uuid",
  "program_id": "uuid",
  "target": {"designation": "T UMi"},
  "window_start_utc": "2026-07-22T02:00:00Z",
  "window_end_utc": "2026-07-22T03:30:00Z",
  "predicted_altitude_deg": 45.2,
  "airmass": 1.4,
  "status": "agendado",
  "status_reason": null,
  "instrument_config_id": "uuid",
  "priority": 10,
  "notes": ""
}
```

### 3.6 Sessão (`ExecutarSessao` — Desktop origina)

| Método | Path | Descrição |
|--------|------|-----------|
| POST | `/sessions` | Registrar início (Desktop) |
| PATCH | `/sessions/{id}` | Atualizar / encerrar |
| POST | `/sessions/{id}/events` | Eventos de bloco |
| GET | `/sessions/{id}` | Detalhe + snapshot do plano |

**Iniciar sessão (Desktop ? SaaS):**

```json
{
  "site_id": "uuid",
  "daily_plan_id": "uuid",
  "daily_plan_version": 7,
  "started_at_utc": "2026-07-22T01:55:00Z",
  "device_id": "uuid",
  "meteo_snapshot": {
    "cloud_cover_pct": 10,
    "wind_ms": 3.2,
    "source": "manual",
    "meteo_manual": false
  }
}
```

**Evento de bloco:**

```json
{
  "type": "block.completed",
  "block_id": "uuid",
  "occurred_at_utc": "2026-07-22T02:45:00Z",
  "payload": {"exposure_count": 12}
}
```

Tipos: `block.started`, `block.completed`, `block.skipped`, `block.failed`, `equipment.changed`.

### 3.7 Observações (`RegistrarObservacao`)

| Método | Path | Descrição |
|--------|------|-----------|
| POST | `/observations` | Criar registro (metadados) |
| GET | `/observations/{id}` | Detalhe |
| GET | `/observations` | Lista filtrada |
| POST | `/observations/{id}/artifacts` | Iniciar upload de FITS |

**Criar observação:**

```json
{
  "id": "uuid",
  "client_id": "desktop-local-uuid",
  "session_id": "uuid",
  "site_id": "uuid",
  "block_id": "uuid",
  "program_id": "uuid",
  "observed_at_utc": "2026-07-22T02:30:15Z",
  "target": {"designation": "T UMi"},
  "instrument_config_id": "uuid",
  "camera_backend": "udrv",
  "simulated": false,
  "meteo_snapshot": {},
  "headers_summary": {"EXPTIME": 60, "FILTER": "V"},
  "artifact": {
    "filename": "T_UMi_20260722_023015.fits",
    "sha256": "...",
    "size_bytes": 16777216
  }
}
```

Resposta inclui `upload_url` (presigned) ou `upload_session_id` para chunks.

### 3.8 Artefatos

| Método | Path | Descrição |
|--------|------|-----------|
| PUT | `/artifacts/upload/{upload_id}` | Upload binário (chunk) |
| POST | `/artifacts/upload/{upload_id}/complete` | Finalizar upload |
| GET | `/artifacts/{id}/download` | URL de download (SaaS UI) |

### 3.9 Análise (`Analisar` — SaaS)

| Método | Path | Descrição |
|--------|------|-----------|
| POST | `/analysis/jobs` | Enfileirar redução/análise |
| GET | `/analysis/products/{id}` | ProdutoAnalise |
| GET | `/analysis/products` | Lista por programa/observação |

### 3.10 Contribuição (`ExportarRede`)

| Método | Path | Descrição |
|--------|------|-----------|
| POST | `/contributions` | Gerar rascunho |
| POST | `/contributions/{id}/validate` | Validar contra atlas |
| POST | `/contributions/{id}/export` | Gerar arquivo |
| GET | `/contributions` | Lista por programa/rede |

---

## 4. Sync API (batch)

Para operação offline-first. Detalhe de política: [MODELO_DE_SINCRONIZACAO.md](MODELO_DE_SINCRONIZACAO.md).

### 4.1 Pull (Desktop ? SaaS)

```http
GET /sync/changes?since={cursor}&site_id={uuid}
```

Resposta:

```json
{
  "cursor": "opaque-token",
  "changes": [
    {
      "entity": "daily_plan",
      "id": "uuid",
      "version": 7,
      "operation": "upsert",
      "payload": {}
    },
    {
      "entity": "program",
      "id": "uuid",
      "version": 5,
      "operation": "upsert",
      "payload": {}
    }
  ]
}
```

### 4.2 Push (Desktop ? SaaS)

```http
POST /sync/batch
{
  "device_id": "uuid",
  "operations": [
    {
      "client_op_id": "local-uuid-1",
      "entity": "observation",
      "operation": "create",
      "payload": {},
      "client_timestamp_utc": "2026-07-22T02:30:15Z"
    },
    {
      "client_op_id": "local-uuid-2",
      "entity": "session_event",
      "operation": "create",
      "payload": {}
    }
  ]
}
```

Resposta:

```json
{
  "results": [
    {"client_op_id": "local-uuid-1", "status": "accepted", "server_id": "uuid"},
    {"client_op_id": "local-uuid-2", "status": "accepted", "server_id": "uuid"}
  ],
  "conflicts": []
}
```

### 4.3 Conflitos

```json
{
  "client_op_id": "local-uuid-3",
  "status": "conflict",
  "reason": "version_mismatch",
  "server_version": 8,
  "resolution_hint": "pull_and_retry"
}
```

---

## 5. Portas de domínio (camada interna)

Além da API HTTP, os mesmos contratos aparecem como **ports** na biblioteca compartilhada:

| Porta | Implementação SaaS | Implementação Desktop |
|-------|-------------------|----------------------|
| `ArchivePort` | PostgreSQL adapter | SQLite adapter |
| `RemoteArchivePort` | — | HTTP client ? Sync API |
| `SyncPort` | Sync API server | Sync client + fila |
| `ArtifactStorePort` | Object storage | Filesystem local |
| `EphemerisPort` | Astropy/Astroquery | Cache + fallback remoto |
| `MeteoPort` | API + manual | Local sensor + manual |
| `CameraPort` | — | Alpyca / udrv / sim |
| `MountPort` | — | Alpyca / sim |
| `FocuserPort` | — | Alpyca / sim |
| `NetworkExportPort` | Exporters SaaS | — (opcional cache) |

---

## 6. Casos de uso ? serviços

| Caso de uso | Serviço SaaS | Serviço Desktop |
|-------------|--------------|-----------------|
| `GerirSite` | `SiteService` | `LocalSiteCache` + sync |
| `GerirProgramas` | `ProgramService` | read-only cache |
| `PlanejarDia` | `PlanningService` | — |
| `ExecutarSessao` | `SessionRegistry` (receive) | `SessionRuntime` |
| `RegistrarObservacao` | `ObservationService` | `AcquisitionService` |
| `Analisar` | `AnalysisService` | — |
| `ExportarRede` | `ContributionService` | — |

---

## 7. Códigos de erro

| HTTP | Código | Significado |
|------|--------|-------------|
| 400 | `validation_error` | Payload inválido |
| 401 | `unauthorized` | Token inválido |
| 403 | `forbidden` | Sem acesso ao workspace |
| 404 | `not_found` | Recurso inexistente |
| 409 | `version_conflict` | Concorrência / sync |
| 422 | `business_rule_violation` | RN-* violada (ex.: export sem produto mínimo) |
| 503 | `service_unavailable` | SaaS em manutenção |

Corpo padrão:

```json
{
  "error": "business_rule_violation",
  "message": "Produto mínimo não atendido para PO-A01",
  "rule_id": "RN-080",
  "details": {}
}
```

---

## 8. Webhooks (futuro)

Para UI web e notificações:

- `observation.created`
- `session.ended`
- `analysis.completed`
- `contribution.validated`

Não necessário na v1 do Desktop.

---

## 9. Versionamento da API

- Path `/v1/` — breaking changes ? `/v2/`
- Campo `version` em entidades mutáveis para optimistic locking
- Desktop declara `X-Client-Version` nas requisições

---

## 10. Histórico

| Versão | Data | Notas |
|--------|------|-------|
| 1.0 | 2026-07-21 | Contratos iniciais SaaS ? Desktop |
