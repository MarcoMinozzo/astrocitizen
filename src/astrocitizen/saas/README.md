# SaaS scaffold (AC-223)

Serviço mínimo alinhado a [API_ALVO.md](../../docs/API_ALVO.md) e
[MODELO_DE_SINCRONIZACAO.md](../../docs/MODELO_DE_SINCRONIZACAO.md).

## Arranque

```bash
pip install 'astrocitizen[saas]'
export ASTROCITIZEN_SAAS_TOKEN=dev-token-change-me
astrocitizen saas serve --host 127.0.0.1 --port 8080
```

Store mestre: SQLite em `~/.local/share/astrocitizen/saas_master.sqlite3`
(ou `ASTROCITIZEN_SAAS_DB`). Postgres chega numa iteração seguinte (mesmo contrato).

## Endpoints

| Método | Path | Auth |
|--------|------|------|
| GET | `/health` | não |
| POST | `/auth/token` | não (devolve token de dev) |
| POST | `/sync/batch` | Bearer |
| GET | `/observations` | Bearer |

## Desktop

```bash
astrocitizen sync enqueue-observation --id <uuid>
astrocitizen sync enqueue-submission --id <uuid>
astrocitizen sync push --url http://127.0.0.1:8080 --token $ASTROCITIZEN_SAAS_TOKEN
astrocitizen sync status
```
