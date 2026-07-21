# Projeto: Plataforma de Astronomia Observacional

**Nome de trabalho:** SBIG Suite → Plataforma Observacional  
**Status:** Projeto inicial (planejamento) — **sem implementação nesta fase**  
**Data:** 2026-07-20  
**Baseline:** `sbig-suite` v0.1.0  

---

## 1. Visão

Transformar o `sbig-suite` — hoje uma suíte de aquisição para câmeras SBIG ST (USB) — numa **plataforma completa de astronomia observacional cidadã (citizen science)**.

### Mandato de escopo (decisão 2026-07-20)

A plataforma **deve cobrir todas as áreas da astronomia observacional praticada por citizen science** com telescópios e pequenos observatórios — não um subconjunto “MVP eterno”.

Isso inclui, no mínimo, o mapa completo de [`REVISAO_ASTRONOMIA_OBSERVACIONAL.md`](REVISAO_ASTRONOMIA_OBSERVACIONAL.md) e o inventário em [`ESCOPO_CITIZEN_SCIENCE.md`](ESCOPO_CITIZEN_SCIENCE.md):

- Fundação (aquisição, calibração, FITS, planejamento, arquivo)
- Fotometria e variáveis; trânsitos; microlensing
- Espectroscopia amadora (slit / ARAS / Be)
- Astrometria, NEOs, supernovas (blink), ocultações (IOTA)
- Imaging lunar/planetário, deep-sky e solar
- Operação de observatório (montagem, focuser, filtros, guiagem; depois cúpula)
- Contribuição às redes (AAVSO, MPC, IOTA, ARAS/BeSS, etc.)
- Rádio-astronomia amadora (eixo paralelo, mesmo produto-plataforma)
- Educação / labs de observação

**Entrega é faseada** (Tiers / P0–P5); **escopo-alvo não é opcional** — cada área entra no roadmap até cobertura completa. Teoria pura, revistas e obra civil de observatório permanecem fora do software (documentação/contexto).

Fontes de domínio:

- `/media/mminozzo/OBERON1/literatura/Astronomia`
- `/media/mminozzo/OBERON1/Espectrografia astronomica`

O `sbig-suite` atual é o **núcleo de aquisição** a partir do qual a plataforma cresce.

### Foco operacional de negócio

A plataforma é centrada em:

1. Obter **dados astronômicos** e **efemérides observacionais**  
2. Obter **meteorologia do local de observação**  
3. Criar o **programa observacional diário**  
4. **Planejar observações** e **planejar equipamento**  
5. **Registrar e analisar** observações  
6. **Gerenciar** os diversos programas observacionais (campanhas cidadãs)
7. **Persistir** todo resultado observacional em **bancos de dados**

Especificação: [`ESCOPO_GERAL_E_REGRAS_DE_NEGOCIO.md`](ESCOPO_GERAL_E_REGRAS_DE_NEGOCIO.md)  
Inventário científico CS-*: [`ESCOPO_CITIZEN_SCIENCE.md`](ESCOPO_CITIZEN_SCIENCE.md)  
**Áreas observacionais oficiais (templates PO-*):** [`PROGRAMAS_OBSERVACIONAIS.md`](PROGRAMAS_OBSERVACIONAIS.md) — decisão 2026-07-20; classes A–K (~53 programas).


### Princípio desta fase

> Documentar visão, escopo, arquitetura-alvo e roadmap. **Não alterar software** até o plano ser revisado e priorizado.

### Princípio de engenharia (D-010)

> Todas as soluções devem privilegiar a **melhor otimização técnica** e o **melhor uso de recursos computacionais** (CPU, RAM, I/O, número de processos, latência no caminho crítico). Alinhamento a outros produtos não prevalece sobre este critério. Detalhe: [`decisoes/D-010-otimizacao-recursos.md`](decisoes/D-010-otimizacao-recursos.md).

---

## 2. Situação atual (baseline)

### O que o sbig-suite já faz (MVP+)

| Capacidade | Estado |
|------------|--------|
| Aquisição (expose light/dark, binning) | Implementado |
| Cooler / regulação térmica | Implementado |
| Roda de filtros (CFW) | Implementado |
| Guider (relays) / AO tip-tilt | Implementado |
| FITS (astropy) + preview | Implementado |
| Stack / calibração básica / sharpen | Implementado |
| Diagnóstico driver/USB | Implementado |
| Backend real (Universal Driver) + simulador | Implementado |
| GUI PySide6 + CLI | Implementado |
| Linux + Windows | Implementado |

### Arquitetura atual

```
UI (PySide6) → services → CameraBackend
                            ├─ UdrvBackend (ctypes → libsbigudrv)
                            └─ SimulatorBackend
```

### Lacunas explícitas no README (já previstas)

- Spectra / DSS-7  
- STV Remote  
- Seeing Monitor  

### Lacunas estruturais para uma plataforma observacional

Além do README, a literatura e a prática observacional exigem módulos que **ainda não existem**:

1. Planejamento de sessão / efemérides / alvos  
2. Sequenciador de observação (scripts de noite)  
3. Calibração CCD completa e rastreável (masters, metadados)  
4. Fotometria (abertura, diferencial, curvas de luz)  
5. Espectroscopia (extração 1D, calibração λ, continuum, linhas)  
6. Astrometria / plate-solving  
7. Programas científicos (variáveis, ocultações, supernovas, exoplanetas, solar)  
8. Arquivo / catálogo interno de observações  
9. Integração com montagem / observatório (além da câmera)  
10. Plugins / extensibilidade sem acoplar tudo ao driver SBIG  

---

## 3. Fontes literárias que orientam o produto

A biblioteca é ampla (teoria, revistas, dados históricos, hardware SBIG). Para o **produto**, priorizamos fontes **operacionais e técnicas** alinhadas a capacidades de software.

### 3.1 Núcleo instrumental e CCD

| Tema | Exemplos na literatura | Implicação na plataforma |
|------|------------------------|--------------------------|
| CCD / aquisição | *A practice guide of CCD*, manuais AAVSO CCD, `ccdops_user_guide`, pasta `ST-7`, `PRATICAS CCD`, `Astronomia Gramadão SBIG` (FITS/ST8 reais) | Workflows de bias/dark/flat; metadados FITS; testes com dados reais do Gramadão |
| Processamento | *Creating and Enhancing Digital Astro Images*, *Digital Astrophotography*, pasta `imagens tratamento`, IRAF | Pipeline de redução; visualização tipo DS9; stack/calibração avançada |
| Hardware SBIG | Pasta `ST-7`, DSS/Spectra (roadmap), Lhires III guide | Manter núcleo SBIG; preparar módulo espectral DSS-7 / espectrógrafos amadores |

### 3.2 Espectroscopia (eixo prioritário da literatura dedicada)

Diretório `Espectrografia astronomica` + pasta `espectroscopia`:

| Fonte (representativa) | Uso no produto |
|------------------------|----------------|
| *Astronomical Spectroscopy for Amateurs* | UX e fluxo amador→profissional |
| Tennyson — *Astronomical Spectroscopy* | Modelo físico de linhas / interpretação |
| Massey & Hanson — *Astronomical Spectroscopy* | Redução e práticas observacionais |
| *Spectrograph design fundamentals* / Schroeder — *Astronomical optics* | Modelo de instrumento (resolução, slit, dispersão) |
| Buil — ISIS / Alpy tutorial; Lhires III User Guide | Referência de pipeline (calibração λ, neon, flats espectrais) |
| Robinson — *Spectroscopy: The Key to the Stars* | Camada didática / interpretação de espectros |
| ARAS Eruptive Stars, 51 Peg b | Casos de uso: monitoramento estelar, RV / exoplanetas |

**Módulo-alvo:** `spectroscopy` — da imagem 2D do espectro à solução em comprimento de onda e medidas de linhas.

### 3.3 Fotometria e variáveis

| Fonte | Uso |
|-------|-----|
| Pasta `fotometria`, *Young Photometry*, AAVSO CCD Manual | Fotometria de abertura / diferencial |
| Pasta `estrelas variaveis`, GCVS types | Programas de variáveis + export AAVSO |
| *CCD Photometry* materials, algoritmos de centroide | Detecção e medição |

**Módulo-alvo:** `photometry` — de frames calibrados a curvas de luz e relatórios.

### 3.4 Astrometria, NEOs, ocultações, supernovas

| Fonte | Uso |
|-------|-----|
| Pasta `astrometrica`, `PRATICAS CCD` (Astrometrica) | Plate-solve, WCS, identificação |
| `OCULTACOES` / IOTA Observers Manual | Timing de alta precisão, séries rápidas |
| `busca de supernovas`, Blink Tutorial | Blink / diferença de imagens |
| Pasta `NEO`, UCAC4 | Catálogos e follow-up |

**Módulos-alvo:** `astrometry`, `timing`, `diffimaging`.

### 3.5 Observatório, automação e sessão

| Fonte | Uso |
|-------|-----|
| *Building a Roll-Off Roof Observatory*, pastas `Observatorio`, `construcao observatorio` | Contexto de operação (não é software de CAD) |
| `telescopio automação`, Gemini Telescope Net | Futura integração montagem/cúpula (fase tardia) |
| *Astronomy with a Home Computer*, *Practical Astronomy with Calculator/Spreadsheet* | Planejamento de noite, efemérides, utilitários |

**Módulo-alvo:** `session` (curto prazo) e `observatory` (longo prazo).

### 3.6 Ciência de suporte (não é UI, mas alimenta análises)

Astrofísica estelar, diagrama HR, exoplanetas, asterosismologia, polarimetria, solar — informam **plugins científicos** e validações, não o núcleo de aquisição.

---

## 4. Arquitetura-alvo da plataforma

Evoluir o monólito atual para uma **plataforma em camadas**, preservando o que já funciona.

**Stack tecnológica adotada** (detalhe em [`STACK_TECNOLOGICA.md`](STACK_TECNOLOGICA.md)):

| Camada | Tecnologia |
|--------|------------|
| Céu, tempo, FITS, redução | **Astropy** |
| Efemérides / NEO / SIMBAD / MPC | **Astroquery** |
| Hardware (montagem, câmera ASCOM, focuser, …) | **ASCOM Alpaca + Alpyca** |
| Câmeras SBIG ST USB | **Universal Driver** (já existente) |
| UI | **PySide6** |

```
┌─────────────────────────────────────────────────────────────┐
│  Apps / UI (PySide6)                                        │
├─────────────────────────────────────────────────────────────┤
│  Domínio científico (plugins)                               │
│  photometry │ spectroscopy │ astrometry │ variables │ …     │
├─────────────────────────────────────────────────────────────┤
│  Pipelines & sessão                                         │
│  calibration │ sequencer │ archive │ planning (Astropy)     │
│  ephemeris (Astroquery: Horizons / MPC / SIMBAD)            │
├─────────────────────────────────────────────────────────────┤
│  Serviços de instrumento                                    │
│  acquisition │ cooling │ filters │ guider │ mount │ focus   │
├─────────────────────────────────────────────────────────────┤
│  Abstrações de hardware                                     │
│  CameraBackend │ MountBackend │ FocuserBackend │ …          │
│  ├─ UdrvBackend (SBIG)                                      │
│  ├─ Alpaca*Backend (Alpyca → HTTP/JSON)                     │
│  └─ Simulator*Backend                                       │
├─────────────────────────────────────────────────────────────┤
│  Dados: **BD(s)** + FITS/artefatos referenciados │ catálogos │
└─────────────────────────────────────────────────────────────┘
```

### Decisões de desenho

1. **Núcleo estável:** `core/` + `services/` de câmera permanecem; novos módulos não quebram CLI/GUI atuais.  
2. **Astropy é a fonte de verdade** para tempo, coordenadas e FITS; o hardware só executa.  
3. **Alpaca/Alpyca é o caminho padrão** de hardware ASCOM (multiplataforma). COM/`pywin32` não é o caminho principal.  
4. **Astroquery** para serviços remotos (Horizons, MPC, SIMBAD); ocultações = efemérides + previsões IOTA + timing local.  
5. **SBIG udrv permanece** backend de primeira classe; Alpaca Camera é complemento, não substituto imediato.  
6. **Dados primeiro:** FITS bem preenchidos; corpus Gramadão para testes.  
7. **Plugins por domínio** com API comum; UI não importa Alpyca/udrv diretamente.  
8. **Simuladores:** SimulatorBackend atual + Alpaca Omni Simulators para montagem/CI.

### Decisões de campo (2026-07-20)

- Montagens **diversas** via Alpaca Telescope (agnóstico de marca).
- Produto em **Linux e Windows**.
- Câmeras: **udrv SBIG** e **Alpaca Camera** (escolha na sessão).
- **Focuser** no escopo.
- Coordenadas do site = **local de observação** configurável (`SiteProfile`), não valor fixo.


### Nome do produto (a decidir)

Opções de trabalho:

- Manter **sbig-suite** como núcleo e nomear a plataforma (**Oberon Observatory Platform**, **AstroSuite**, etc.)  
- Ou evoluir o nome do pacote em major version (`sbig-suite` 1.x → plataforma 2.x)

**Decisão adiada** até revisão deste documento.

---

## 5. Mapa de capacidades (escopo da plataforma)

### P0 — Fundação (fortalecer o que existe)

- [ ] Contratos de API estáveis para `CameraBackend` e services  
- [ ] Headers FITS observacionais completos (objeto, filtro, TEMP, EXPTIME, IMAGETYP, etc.)  
- [ ] Biblioteca de calibração: masters bias/dark/flat + aplicação rastreável  
- [ ] Visualizador FITS (stretch, zoom, ROI, histogramas; inspirado em DS9)  
- [ ] Suite de testes com dados reais (`Astronomia Gramadão SBIG`)  
- [ ] Documentação de workflows de noite (checklist operacional)

### P1 — Sessão observacional

- [ ] Planejador de noite (alvos, altitude, janelas)  
- [ ] Sequenciador: N exposições × filtros × calibração intercalada  
- [ ] Log de sessão / diário de observação  
- [ ] Arquivo local indexado (busca por data, objeto, tipo)

### P2 — Fotometria

- [ ] Detecção / centroide  
- [ ] Abertura e anéis de céu  
- [ ] Fotometria diferencial e curvas de luz  
- [ ] Export AAVSO / CSV  
- [ ] Programa **estrelas variáveis** (templates de campanha)

### P3 — Espectroscopia

- [ ] Extração de espectro 1D a partir da imagem 2D  
- [ ] Calibração em comprimento de onda (lâmpada / linhas conhecidas)  
- [ ] Correção de continuum / resposta instrumental  
- [ ] Medidas de linhas (EW, centroide, Doppler básico)  
- [ ] Perfis para Lhires / Alpy / DSS-7 (quando hardware disponível)  
- [ ] Casos: Be/ARAS, exoplanetas (RV educacional), classificação espectral

### P4 — Astrometria e programas especiais

- [ ] Plate-solving / WCS  
- [ ] Blink / diferença (supernovas, asteroides)  
- [ ] Timing de ocultações (IOTA-oriented)  
- [ ] Seeing monitor (já no roadmap README)

### P5 — Observatório e extensões

- [ ] Integração montagem via **ASCOM Alpaca + Alpyca** (`MountBackend`)  
- [ ] Câmera ASCOM opcional (`AlpacaCameraBackend`) além do udrv SBIG  
- [ ] Focuser / FilterWheel / ObservingConditions (Alpaca)  
- [ ] STV Remote / periféricos SBIG restantes  
- [ ] Polarimetria / solar / fast photometry (plugins avançados)  
- [ ] Automação de cúpula / remoto (Dome/Switch Alpaca)

---

## 6. Roadmap por fases

| Fase | Nome | Objetivo | Duração sugerida | Entregáveis |
|------|------|----------|------------------|-------------|
| **0** | Projeto (atual) | Acordo de visão e prioridades | 1–2 semanas | Este documento revisado; backlog priorizado |
| **1** | Fundação de dados | FITS + calibração + viewer + testes Gramadão | 4–6 semanas | Pipeline de calibração usável; corpus de testes |
| **2** | Sessão | Sequenciador + arquivo | 4–6 semanas | Noite automatizada na câmera SBIG |
| **3** | Fotometria | Medição e curvas de luz | 6–8 semanas | Módulo photometry + export |
| **4** | Espectroscopia | Redução espectral amadora | 8–12 semanas | Módulo spectroscopy MVP |
| **5** | Programas A | Variáveis, blink, NEO/MPC, ocultações IOTA | contínuo | Plugins + export redes |
| **6** | Programas B | Trânsitos, imaging, solar, microlensing | contínuo | Plugins |
| **7** | Observatório | Montagem/focuser Alpaca, remoto, cúpula | contínuo | Adapters |
| **8** | Rádio + nichos | Rádio cidadão, polarimetria, echelle | contínuo | Eixo paralelo / plugins |

As fases científicas podem **sobrepor-se**. Nenhuma área de `ESCOPO_CITIZEN_SCIENCE.md` fica de fora do plano — apenas mais tarde na fila.

---

## 7. Riscos e restrições

| Risco | Mitigação |
|-------|-----------|
| Escopo amplo (toda citizen science) | Escopo fechado em `ESCOPO_CITIZEN_SCIENCE.md`; teoria/revistas/obra civil fora; entrega por ondas |
| Driver SBIG proprietário | Manter simulador; documentar limites; não redistribuir binários |
| Reinventar IRAF/ISIS/Astrometrica | Interoperar e reutilizar algoritmos; focar na UX unificada e no hardware SBIG |
| UI monolítica inchada | Arquitetura de módulos/plugins desde a Fase 1 |
| Falta de hardware espectral | Desenvolver com dados sintéticos + frames públicos/arquivados |

---

## 8. Critérios de sucesso

### 8.1 Cobertura citizen science (definição de “plataforma completa”)

A plataforma só é considerada **completa** quando um cidadão-cientista conseguir, **no mesmo ambiente** (Linux ou Windows), executar e contribuir em **todas** as áreas listadas em `ESCOPO_CITIZEN_SCIENCE.md` — com backends reais e/ou simulador.

Checklist-resumo (todas obrigatórias a longo prazo):

| Domínio | Critério mínimo de cobertura |
|---------|------------------------------|
| Fundação | Noite completa: planejar → adquirir → calibrar → arquivar |
| Hardware | Montagem Alpaca, câmera udrv **e** Alpaca, focuser; site por local |
| Fotometria | Diferencial + export AAVSO; variáveis |
| Espectroscopia | Slit 1D λ-calibrado + medida de linha; fluxo tipo ARAS |
| Astrometria / NEO / SN | Plate-solve / WCS; blink; export MPC quando aplicável |
| Ocultações | Timing + relatório orientado IOTA |
| Exoplanetas | Curva de trânsito; (depois) apoio a microlensing |
| Imaging | Lunar/planetário e deep-sky; solar seguro |
| Observatório | Sequenciador; guiagem; condições; caminho a cúpula/remoto |
| Redes | Export/formatos das redes cidadãs relevantes |
| Rádio | Fluxo educacional amador (eixo paralelo) |
| Educação | Roteiros de lab / sessão guiada |
| CI | Simuladores cobrindo fluxos críticos sem hardware |

### 8.2 Marcos intermediários (não confundir com escopo final)

Marcos (ex.: “primeira noite SBIG + fotometria”) medem **progresso**, não reduzem o mandato §1. Polarimetria, echelle e automação total de cúpula podem ser os últimos plugins, mas **permanecem no escopo** até cobertos ou explicitamente adiados por decisão documentada.

---

## 9. Organização do trabalho (próximos passos — sem código ainda)

### Imediatamente (revisão humana)

1. Validar visão e definição de sucesso (§1, §8).  
2. Escolher prioridade entre **fotometria** e **espectroscopia** após a Fundação (Fase 1).  
3. Decidir nome da plataforma e se o repositório permanece `sbig-suite` ou ganha um umbrella.  
4. Inventariar hardware disponível (câmeras ST, CFW, espectrógrafo Lhires/Alpy/DSS, montagem).  
5. Selecionar um **corpus mínimo** de dados de teste a partir do Gramadão + espectros de exemplo.

### Artefatos da Fase 0 (documentação)

| Artefato | Descrição |
|----------|-----------|
| `docs/PLATAFORMA_OBSERVACIONAL.md` | Este documento (visão e roadmap) |
| `docs/ESCOPO_CITIZEN_SCIENCE.md` | Inventário completo CS-* (mandato) |
| `docs/ESCOPO_GERAL_E_REGRAS_DE_NEGOCIO.md` | Escopo geral + regras RN-* |
| `docs/PROGRAMAS_OBSERVACIONAIS.md` | Catálogo classificado de programas PO-* |
| `docs/PERSISTENCIA_E_BANCOS.md` | Todo resultado → bancos de dados |
| `docs/BACKLOG.md` | Fila de implementação |
| `docs/LITERATURA_INDICE.md` | Índice curado: obra → módulo |
| `docs/STACK_TECNOLOGICA.md` | Astropy / Alpyca / Astroquery |
| `docs/WORKFLOWS.md` | Jornada do usuário e fluxos-alvo |
| `docs/ARQUITETURA_SAAS_DESKTOP.md` | Módulos SaaS + Desktop |
| `docs/API_ALVO.md` | Contratos Desktop ↔ SaaS |
| `docs/MODELO_DE_SINCRONIZACAO.md` | Sincronização offline-first |
| `docs/MODELO_DADOS_V1.md` | Schema relacional v1 |
| `docs/AVALIACAO_STACK_MOTORSPORT.md` / D-009 / D-010 | Stack SaaS + otimização |
| `docs/COMPARACAO_DESKTOP_TAURI_VS_PYSIDE.md` | Desktop = PySide6 |
| `docs/ascom/` | Espelho ASCOM + mapeamento equipamento |
| `docs/TEST_BACKLOG.md` | Testes hardware |
| `docs/ascom/MAPEAMENTO_EQUIPAMENTO_ASCOM.md` | Hardware → ASCOM → driver → porta Desktop |

### Explicitamente fora desta fase

- Alterações em `src/`, testes, CI, empacotamento  
- Refactors ou novas features no software  
- Migração de dados ou instalação de dependências novas  

---

## 10. Resumo executivo

O `sbig-suite` já resolve o **controle e aquisição SBIG**. A decisão de produto é transformá-lo numa **plataforma que cubra toda a astronomia observacional de citizen science** (ver `ESCOPO_CITIZEN_SCIENCE.md`): fundação, fotometria, espectroscopia, astrometria/NEO/SN, ocultações, exoplanetas, imaging, solar, hardware multi-montagem, redes cidadãs, rádio e educação.

A **entrega é faseada**; o **escopo-alvo não é parcial**. A implementação de código começa somente após fechar a Fase 0 de documentação.


---

## Apêndice A — Inventário rápido da literatura por pasta temática

| Pasta / coleção | Relevância |
|-----------------|------------|
| `Espectrografia astronomica/` | Alta — base teórica e prática do módulo spectral |
| `Astronomia/espectroscopia/` | Alta — ARAS, tutoriais, casos |
| `Astronomia/fotometria/` | Alta |
| `Astronomia/PRATICAS CCD/` | Alta — laboratório e astrometria |
| `Astronomia/material CCD/`, `ST-7/` | Alta — hardware e CCDOPS legado |
| `Astronomia/Astronomia Gramadão SBIG/` | Alta — dados reais para testes |
| `Astronomia/estrelas variaveis/` | Média-alta — programa científico |
| `Astronomia/OCULTACOES/` | Média — timing |
| `Astronomia/busca de supernovas/` | Média — blink |
| `Astronomia/IRAF/`, `imagens tratamento/` | Média — referência de redução |
| `Astronomia/telescopio automação/` | Baixa-média — fase observatório |
| Revistas *Sky & Telescope* / *Astronomy* | Baixa — inspiração, não requisitos |
| Astrofísica teórica geral | Baixa para produto — alta para interpretação científica |

## Apêndice B — Stack técnica atual (a preservar)

- Python ≥ 3.10  
- PySide6  
- numpy, astropy  
- pytest, PyInstaller, GitHub Actions  
- Licença MIT no código da suíte; Universal Driver **não** redistribuído  

Dependências futuras candidatas (avaliação; instalar só na fase de implementação): `alpyca`, `astroquery`, `scipy`, `matplotlib`/`pyqtgraph`, `photutils`, `specutils`, wrappers astrometry.net / plate-solve.

Ver stack completa: [`STACK_TECNOLOGICA.md`](STACK_TECNOLOGICA.md).
