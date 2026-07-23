# Índice da documentação — AstroCitizen

## Comece por aqui

1. [PRODUCT_BACKLOG.md](PRODUCT_BACKLOG.md) — o que construir e em que ordem  
2. [TEST_BACKLOG.md](TEST_BACKLOG.md) — testes com hardware real (pendentes de campo)  
3. [ARQUITETURA.md](ARQUITETURA.md) — como estruturar o software  
4. [ESCOPO_GERAL_E_REGRAS_DE_NEGOCIO.md](ESCOPO_GERAL_E_REGRAS_DE_NEGOCIO.md) — regras RN-*  
5. [PROGRAMAS_OBSERVACIONAIS.md](PROGRAMAS_OBSERVACIONAIS.md) — programas oficiais PO-*  
6. [MODELO_DADOS_V1.md](MODELO_DADOS_V1.md) — schema BD v1  

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

## Produto e jornada

| Doc | Descrição |
|-----|-----------|
| [WORKFLOWS.md](WORKFLOWS.md) | Jornada do usuário, modos, fluxos passo a passo, PO-A01 referência |
| [ENTRADA_OBSERVACOES_POR_PO.md](ENTRADA_OBSERVACOES_POR_PO.md) | Como o utilizador fornece dados por cada PO-* (canais IN-*) |
| [DESKTOP_UI_DESIGN.md](DESKTOP_UI_DESIGN.md) | IA e design do shell PySide6 (pos-ENTRADA; 6 areas) |
| [SPRINT_DESKTOP_UI_U0_U1.md](SPRINT_DESKTOP_UI_U0_U1.md) | Sprint U0/U1: widgets + nav 6 areas |
| [SPRINT_DESKTOP_UI_U2.md](SPRINT_DESKTOP_UI_U2.md) | Sprint U2: Import hub + ContextBar sync |
| [SPRINT_DESKTOP_UI_U3_U4.md](SPRINT_DESKTOP_UI_U3_U4.md) | Sprint U3/U4: Arquivo + Analisar + Viewer FITS |
| [SPRINT_DESKTOP_UI_U5.md](SPRINT_DESKTOP_UI_U5.md) | Sprint U5: plots + Arquivo detalhe/export hint |
| [SPRINT_PROGRAMA_ACTIVO.md](SPRINT_PROGRAMA_ACTIVO.md) | Guia Programa activo + atalho Contribuir |
| [SPRINT_I18N_HELP.md](SPRINT_I18N_HELP.md) | RN-120/121: idiomas pt/es/en + Ajuda in-app |
| [SPRINT_PLATESOLVE_AC110.md](SPRINT_PLATESOLVE_AC110.md) | Plate-solve + bridge GUI |
| [SPRINT_MEASURE_ASTROMETRY_GUI.md](SPRINT_MEASURE_ASTROMETRY_GUI.md) | Medida astrometria GUI (x,y → RA/Dec) |
| [SPRINT_ARQUIVO_OPEN_EXPORT.md](SPRINT_ARQUIVO_OPEN_EXPORT.md) | Arquivo: abrir artefacto + export directo |
| [SPRINT_RADIO_AC161.md](SPRINT_RADIO_AC161.md) | Radio I02–I04 (espectro / scan / lab notes) |
| [SPRINT_PO_G01_DUPLAS.md](SPRINT_PO_G01_DUPLAS.md) | Duplas PO-G01 (PA/sep / AC-152) |
| [SPRINT_AC190_KB_SCAFFOLD.md](SPRINT_AC190_KB_SCAFFOLD.md) | E19 KB-0 scaffold knowledge-base |
| [SPRINT_AC141_D011.md](SPRINT_AC141_D011.md) | AC-141 validacao redes + D-011 ferramentas imagem |
| [SPRINT_R2_REVISAR_CAMPOS.md](SPRINT_R2_REVISAR_CAMPOS.md) | R2: Revisar campos atlas (AAVSO/MPC) |
| [SPRINT_EXP_WDS.md](SPRINT_EXP_WDS.md) | EXP-WDS: export + Revisar campos (PO-G01) |
| [SPRINT_R3_REVISAR_CAMPOS.md](SPRINT_R3_REVISAR_CAMPOS.md) | R3: Revisar campos TNS/ExoClock/BeSS/IOTA |
| [decisoes/D-011-imagem-ferramentas-externas.md](decisoes/D-011-imagem-ferramentas-externas.md) | Decisao: imagem via ferramentas externas |
| [ANALISE_ESPECTRAL_ASSISTIDA.md](ANALISE_ESPECTRAL_ASSISTIDA.md) | AC-106: como funciona a interpretacao espectral (sem LLM) |
| [EPICO_E19_BASE_CONHECIMENTO_RAG.md](EPICO_E19_BASE_CONHECIMENTO_RAG.md) | Epico E19: base interna de conhecimento para RAG |
| [AAVSO_WEBOBS_CHECKLIST.md](AAVSO_WEBOBS_CHECKLIST.md) | Validar export Extended no WebObs |

## Arquitetura SaaS + Desktop

| Doc | Descrição |
|-----|-----------|
| [ARQUITETURA_SAAS_DESKTOP.md](ARQUITETURA_SAAS_DESKTOP.md) | Dois módulos: cloud (workspace, BD, análise) e desktop (observatório) |
| [AVALIACAO_STACK_MOTORSPORT.md](AVALIACAO_STACK_MOTORSPORT.md) | Stack motorsport → AstroCitizen; BDaaS |
| [COMPARACAO_DESKTOP_TAURI_VS_PYSIDE.md](COMPARACAO_DESKTOP_TAURI_VS_PYSIDE.md) | Desktop: PySide6 vs Tauri+sidecar |
| [../packaging/README.md](../packaging/README.md) | PyInstaller `.exe` Windows (AC-075/076) |
| [API_ALVO.md](API_ALVO.md) | Contratos REST Desktop ↔ SaaS |
| [MODELO_DE_SINCRONIZACAO.md](MODELO_DE_SINCRONIZACAO.md) | Offline-first, fila, conflitos |

## Tecnologia e dados

| Doc | Descrição |
|-----|-----------|
| [STACK_TECNOLOGICA.md](STACK_TECNOLOGICA.md) | Astropy, Alpyca, Astroquery, meteo, BD |
| [PERSISTENCIA_E_BANCOS.md](PERSISTENCIA_E_BANCOS.md) | Persistência obrigatória |
| [MODELO_DADOS_V1.md](MODELO_DADOS_V1.md) | Schema relacional v1 (tabelas, JSONB, índices, Parquet) |
| [ascom/README.md](ascom/README.md) | Espelho documentação ASCOM/Alpaca (hardware Desktop) |
| [ascom/MAPEAMENTO_EQUIPAMENTO_ASCOM.md](ascom/MAPEAMENTO_EQUIPAMENTO_ASCOM.md) | Equipamento → interface ASCOM → driver → porta |
| [decisoes/](decisoes/) | Registro de decisões (ADRs leves) |

## Decisões registradas

| ID | Decisão |
|----|---------|
| D-001 | Nome do produto/repo: **astrocitizen** (separado do sbig-suite) |
| D-002 | Áreas observacionais oficiais = catálogo PO-* |
| D-003 | Arquitetura: monólito modular + hexagonal + DDD + plugins |
| D-004 | Todo resultado observacional alimenta BD(s) |
| D-005 | Stack: Astropy + Astroquery + Alpyca/Alpaca + udrv SBIG (adapter) |
| D-006 | Linux e Windows; montagens diversas; duas vias de câmera; focuser; site por local; **`.exe` Windows** |
| D-007 | Atlas de reporte às redes cidadãs |
| D-008 | Dois módulos: **SaaS** (workspace, BD, análise) + **Desktop** (observatório, hardware) |
| D-009 | Stack motorsport SaaS (FastAPI/Next/Postgres BDaaS); Desktop ver D-009.4-rev |
| D-009.4-rev | Desktop = **PySide6** (não Tauri+sidecar no MVP); `.exe` Windows obrigatório |
| D-010 | **Otimização técnica e uso eficiente de recursos** — critério transversal de desenho |
