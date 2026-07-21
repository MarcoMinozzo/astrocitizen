# AstroCitizen

**Plataforma de astronomia observacional para citizen science**

AstroCitizen é o produto que transforma a operação de pequenos telescópios e observatórios em um fluxo completo:

**efemérides + meteorologia do site → programa diário → planejamento de equipamento → aquisição → registro → análise → bancos de dados → contribuição às redes cidadãs**

Repositório **independente** do `sbig-suite` (que permanece o núcleo de aquisição SBIG e poderá ser integrado como adapter).

---

## Estado atual

Fase **0 — especificação**: documentação de domínio, escopo, regras de negócio, programas observacionais (PO-*), stack tecnológica, persistência e backlog de produto.

**Nenhuma implementação de software de aplicação nesta fase** — apenas documentação e backlog.

---

## Documentação

| Documento | Conteúdo |
|-----------|----------|
| [docs/INDEX.md](docs/INDEX.md) | Índice da documentação |
| [docs/PRODUCT_BACKLOG.md](docs/PRODUCT_BACKLOG.md) | **Backlog do produto** |
| [docs/ARQUITETURA.md](docs/ARQUITETURA.md) | Arquitetura (hexagonal + monólito modular + DDD) |
| [docs/PLATAFORMA_OBSERVACIONAL.md](docs/PLATAFORMA_OBSERVACIONAL.md) | Visão e roadmap |
| [docs/ESCOPO_GERAL_E_REGRAS_DE_NEGOCIO.md](docs/ESCOPO_GERAL_E_REGRAS_DE_NEGOCIO.md) | Escopo geral + regras RN-* |
| [docs/ESCOPO_CITIZEN_SCIENCE.md](docs/ESCOPO_CITIZEN_SCIENCE.md) | Capacidades citizen science |
| [docs/PROGRAMAS_OBSERVACIONAIS.md](docs/PROGRAMAS_OBSERVACIONAIS.md) | Áreas/programas oficiais PO-* |
| [docs/STACK_TECNOLOGICA.md](docs/STACK_TECNOLOGICA.md) | Astropy, Alpyca, Astroquery, BD |
| [docs/PERSISTENCIA_E_BANCOS.md](docs/PERSISTENCIA_E_BANCOS.md) | Todo resultado → bancos de dados |
| [docs/REVISAO_ASTRONOMIA_OBSERVACIONAL.md](docs/REVISAO_ASTRONOMIA_OBSERVACIONAL.md) | Revisão da literatura |
| [docs/LITERATURA_INDICE.md](docs/LITERATURA_INDICE.md) | Índice literatura → módulos |

---

## Princípios

1. Cobrir as **áreas observacionais oficiais** (catálogo PO-*, classes A–K).
2. Operar com **programa diário**, meteo do local, planejamento de equipamento.
3. **Todo resultado observacional alimenta bancos de dados**.
4. Hardware via **ASCOM Alpaca/Alpyca** + backend SBIG (udrv) quando aplicável.
5. Linux **e** Windows; montagens diversas; câmeras udrv e Alpaca; focuser no escopo.
6. Arquitetura: **monólito modular + hexagonal + DDD + plugins PO-***.

---

## Relação com sbig-suite

| Repo | Papel |
|------|--------|
| **astrocitizen** | Produto plataforma (planejamento, programas, BD, análise, redes) |
| **sbig-suite** | Suíte/driver de aquisição SBIG ST (USB) — candidato a adapter `CameraPort` |

Não misturar histórico nem código base neste repositório.

---

## Licença

MIT (código futuro). Material de literatura citado permanece com seus detentores de direitos; aqui só há referências e índices.
