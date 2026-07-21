# Índice da documentação — AstroCitizen

## Comece por aqui

1. [PRODUCT_BACKLOG.md](PRODUCT_BACKLOG.md) — o que construir e em que ordem  
2. [ARQUITETURA.md](ARQUITETURA.md) — como estruturar o software  
3. [ESCOPO_GERAL_E_REGRAS_DE_NEGOCIO.md](ESCOPO_GERAL_E_REGRAS_DE_NEGOCIO.md) — regras RN-*  
4. [PROGRAMAS_OBSERVACIONAIS.md](PROGRAMAS_OBSERVACIONAIS.md) — programas oficiais PO-*  

## Visão e domínio

| Doc | Descrição |
|-----|-----------|
| [PLATAFORMA_OBSERVACIONAL.md](PLATAFORMA_OBSERVACIONAL.md) | Visão, mandato, roadmap |
| [ESCOPO_CITIZEN_SCIENCE.md](ESCOPO_CITIZEN_SCIENCE.md) | Inventário de capacidades CS-* |
| [REVISAO_ASTRONOMIA_OBSERVACIONAL.md](REVISAO_ASTRONOMIA_OBSERVACIONAL.md) | Revisão da literatura |
| [LITERATURA_INDICE.md](LITERATURA_INDICE.md) | Literatura → módulos |

## Reporte às redes (atlas)

| Doc | Descrição |
|-----|-----------|
| [atlas/ATLAS_REPORTE_OBSERVACOES.md](atlas/ATLAS_REPORTE_OBSERVACOES.md) | Formulários, formatos e dados oficiais por rede |
| [atlas/README.md](atlas/README.md) | Índice do atlas |

## Tecnologia e dados

| Doc | Descrição |
|-----|-----------|
| [STACK_TECNOLOGICA.md](STACK_TECNOLOGICA.md) | Astropy, Alpyca, Astroquery, meteo, BD |
| [PERSISTENCIA_E_BANCOS.md](PERSISTENCIA_E_BANCOS.md) | Persistência obrigatória |
| [decisoes/](decisoes/) | Registro de decisões (ADRs leves) |

## Decisões registradas

| ID | Decisão |
|----|---------|
| D-001 | Nome do produto/repo: **astrocitizen** (separado do sbig-suite) |
| D-002 | Áreas observacionais oficiais = catálogo PO-* |
| D-003 | Arquitetura: monólito modular + hexagonal + DDD + plugins |
| D-004 | Todo resultado observacional alimenta BD(s) |
| D-005 | Stack: Astropy + Astroquery + Alpyca/Alpaca + udrv SBIG (adapter) |
| D-006 | Linux e Windows; montagens diversas; duas vias de câmera; focuser; site por local |
