# D-009 — Stack alinhada ao Motorsport Agent + BDaaS

**Data:** 2026-07-21  
**Status:** aceito (emenda Desktop: [D-009.4-rev](D-009.4-rev-desktop-pyside.md))

## Contexto

O AstroCitizen precisa de SaaS + Desktop. Já existe stack madura em `motorsport-agent` / `client-motorsport-agent` (FastAPI, Next.js, PostgreSQL DBaaS, Tauri 2).

## Decisão

1. **SaaS:** mesmo stack de plataforma do motorsport (FastAPI + Next.js + SQLAlchemy/Alembic + PostgreSQL).  
2. **Produção:** bancos e storage geridos (**BDaaS** / object storage as a service).  
3. **Semi-estruturado:** JSONB no Postgres; séries ? Parquet em object store (faseado).  
4. **Desktop (emenda D-009.4-rev):** **PySide6 + Python** (UI + hardware + sync no mesmo processo); Tauri opcional futuro.  
5. Desktop local: SQLite + filesystem (não BDaaS).  
6. **DoD Windows:** `.exe` via PyInstaller (AC-075/076).  
7. Critério transversal: [D-010](D-010-otimizacao-recursos.md).

## Consequências

- Documentação: `AVALIACAO_STACK_MOTORSPORT.md`, `COMPARACAO_DESKTOP_TAURI_VS_PYSIDE.md`, `MODELO_DADOS_V1.md`.  
- Sync Desktop espelha o *comportamento* do Tauri motorsport (fila offline), implementado em Python.  
- SaaS reutiliza padrões FastAPI/Next/Postgres DBaaS do motorsport.

## Alternativas rejeitadas

- Reimplementar hardware em Rust (Tauri-only).  
- Tauri + sidecar Python como Desktop MVP (custo de recursos / IPC — D-010).  
- MongoDB como BD mestre no MVP.
