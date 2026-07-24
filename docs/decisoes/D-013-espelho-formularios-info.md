# D-013 — Espelho SaaS, formulários atlas e serviços de informação

**Data:** 2026-07-23  
**Estado:** aceite  
**Contexto:** além do hub externo ([D-012](D-012-hub-integrations.md)), o produto precisa de
cópia própria das observações, UI de registo alinhada às APIs e consumo interno
dos dados institucionais. Complementa [D-008](D-008-saas-desktop.md) e
[MODELO_DE_SINCRONIZACAO.md](../MODELO_DE_SINCRONIZACAO.md).

## Decisão

AstroCitizen opera em **três pilares** sobre o modelo canónico
(`Observation` / `Spectrum`):

1. **Espelho no nosso servidor (SaaS)**  
   Toda preparação/publicação numa rede gera artefacto + `NetworkSubmission`
   local e enfileira cópia canónica para o BD mestre (`sync_queue` →
   `POST /sync/batch`). O Desktop SQLite é edge/cache; o Postgres SaaS é
   fonte de consulta colaborativa (RN-112). Aquisição **não** depende do SaaS.

2. **Formulários compatíveis com as APIs**  
   Cada rede tem `form_schema.json` (campos atlas / AC-141). FieldReview e CLI
   `contribute form-schema` leem o schema; validação antes de
   `prepare_*` / export. O domínio **não** guarda AEF/ADES — só canónico +
   artefacto gerado.

3. **Serviços de informação internos**  
   Consultas VSX/SIMBAD/AID/… são persistidas em cache próprio
   (`institutional_cache` no Desktop; BD mestre no SaaS). A UI e APIs internas
   leem o **nosso** cache, não fazem proxy opaco sem persistência. Jobs de
   ingest (fase posterior) alimentam o cache a partir dos providers.

## Fluxo

```text
Formulario (schema rede)
  → Observation / Spectrum
  → integrations.provider.prepare_*  → ficheiro oficial + WebObs/REST
  → NetworkSubmission + sync_queue   → SaaS BD mestre
  → institutional_cache (search)     → info service interno
```

## Anti-padrões

- Publicar numa rede sem registo local / sem intenção de sync
- Formulário ad hoc sem schema versionado
- Proxy directo VSX→UI sem gravar cache
- Bloquear noite offline à espera do SaaS

## Relacionados

- D-012 hub · D-008 SaaS+Desktop · E20 / **E21** backlog  
- Código: `integrations/*/form_schema.json`, `institutional_cache`, sync (AC-222+)
