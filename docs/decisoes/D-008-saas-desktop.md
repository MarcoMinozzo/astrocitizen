# D-008 — Arquitetura SaaS + Desktop

**Data:** 2026-07-21  
**Status:** aceito

## Contexto

A plataforma precisa servir dois contextos operacionais distintos:

- gestão científica, planejamento, arquivo e contribuição (acesso via browser, dados centralizados);
- operação do observatório com hardware local, baixa latência e tolerância a falha de internet.

## Decisão

O AstroCitizen será composto por **dois módulos de produto**:

1. **AstroCitizen SaaS** — workspace, programas PO-*, BD mestre, planejamento, análise, documentação, exportação.
2. **AstroCitizen Desktop** — execução de sessão, controle de equipamento, aquisição, cache local e sincronização com o SaaS.

O **domínio** (entidades, RN-*, plugins PO-*) permanece **único**, em biblioteca compartilhada. Cada módulo implementa adapters e casos de uso conforme sua responsabilidade.

## Consequências

- Novo deployable SaaS (API + web + PostgreSQL + object storage).
- Desktop passa a ser edge client com SQLite local e fila de sync.
- Hardware ports (`CameraPort`, `MountPort`, …) existem **apenas no Desktop**.
- D-003 (hexagonal + DDD) aplica-se dentro de cada módulo e no pacote `domain`.
- Documentação: `ARQUITETURA_SAAS_DESKTOP.md`, `API_ALVO.md`, `MODELO_DE_SINCRONIZACAO.md`.

## Alternativas rejeitadas

- **Monólito desktop-only:** impede workspace remoto e colaboração futura.
- **SaaS-only com hardware na nuvem:** inviável para latência e drivers locais (SBIG, Alpaca).
- **Dois domínios divergentes:** duplicaria regras RN-* e PO-*.
