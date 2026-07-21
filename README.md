# AstroCitizen

**Plataforma de astronomia observacional para citizen science**

AstroCitizen é o produto que transforma a operação de pequenos telescópios e observatórios em um fluxo completo:

**efemérides + meteorologia do site → programa diário → planejamento de equipamento → aquisição → registro → análise → bancos de dados → contribuição às redes cidadãs**

Repositório **independente** do `sbig-suite` (que permanece o núcleo de aquisição SBIG e poderá ser integrado como adapter).

---

## Estado atual

Fase **0 — especificação** (fechamento documental): domínio, regras RN-*, programas PO-*, arquitectura SaaS+Desktop, stack, BDaaS, modelo de dados v1, workflows, ASCOM, backlog e testes de hardware.

**Implementação de aplicação** ainda não iniciada (skeleton Python mínimo pode existir). Próximo: Fase 1 / sprints S0–S1 do backlog.

---

## Arquitectura de produto (resumo)

| Módulo | Stack | Papel |
|--------|-------|--------|
| **SaaS** | FastAPI + Next.js + PostgreSQL/object storage **BDaaS** | Workspace, programas, planejamento, arquivo, análise, export |
| **Desktop** | **PySide6** + Python (Alpyca/udrv/Astropy) + PyInstaller → **`.exe` Windows** | Sessão, hardware, aquisição, sync offline (SQLite) |

Princípios: **D-010** (otimização de recursos) · **D-009.4-rev** (PySide, não Tauri+sidecar) · DoD Desktop = executável Windows utilizável.

---

## Documentação

Comece por [docs/INDEX.md](docs/INDEX.md).

| Documento | Conteúdo |
|-----------|----------|
| [docs/PRODUCT_BACKLOG.md](docs/PRODUCT_BACKLOG.md) | Backlog do produto |
| [docs/TEST_BACKLOG.md](docs/TEST_BACKLOG.md) | Testes com hardware (TEST-HW-*) |
| [docs/WORKFLOWS.md](docs/WORKFLOWS.md) | Jornada do utilizador |
| [docs/ARQUITETURA_SAAS_DESKTOP.md](docs/ARQUITETURA_SAAS_DESKTOP.md) | SaaS + Desktop |
| [docs/MODELO_DADOS_V1.md](docs/MODELO_DADOS_V1.md) | Schema BD v1 |
| [docs/API_ALVO.md](docs/API_ALVO.md) | Contratos API Sync |
| [docs/MODELO_DE_SINCRONIZACAO.md](docs/MODELO_DE_SINCRONIZACAO.md) | Offline-first |
| [docs/STACK_TECNOLOGICA.md](docs/STACK_TECNOLOGICA.md) | Astropy, Alpyca, BDaaS |
| [docs/ascom/](docs/ascom/README.md) | ASCOM/Alpaca (espelho + mapeamento) |
| [docs/atlas/ATLAS_REPORTE_OBSERVACOES.md](docs/atlas/ATLAS_REPORTE_OBSERVACOES.md) | Formatos oficiais de reporte |
| [docs/decisoes/](docs/decisoes/) | ADRs (D-001…D-010) |

---

## Princípios

1. Cobrir as **áreas observacionais oficiais** (catálogo PO-*, classes A–K).
2. Operar com **programa diário**, meteo do local, planejamento de equipamento.
3. **Todo resultado observacional alimenta bancos de dados** (BDaaS em produção SaaS).
4. Hardware via **ASCOM Alpaca/Alpyca** + backend SBIG (udrv) quando aplicável.
5. Linux **e** Windows; montagens diversas; `.exe` Windows obrigatório (AC-075/076).
6. Arquitectura: **monólito modular + hexagonal + DDD + plugins PO-***; deploy SaaS + Desktop.
7. **Otimização técnica e uso eficiente de recursos** (D-010).

---

## Relação com sbig-suite

| Repo | Papel |
|------|--------|
| **astrocitizen** | Produto plataforma (planejamento, programas, BD, análise, redes, Desktop PySide) |
| **sbig-suite** | Suíte/driver de aquisição SBIG ST (USB) — candidato a adapter `CameraPort` |

Não misturar histórico nem código base neste repositório.

---

## Licença

MIT (código futuro). Material de literatura citado permanece com seus detentores de direitos; aqui só há referências e índices. Documentação ASCOM espelhada: copyright ASCOM Initiative — uso de referência interna.
