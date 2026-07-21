# Stack tecnológica adotada

**Status:** decisão de arquitetura (Fase 0) — ainda sem implementação  
**Data:** 2026-07-20  
**Relacionados:** `REVISAO_ASTRONOMIA_OBSERVACIONAL.md`, `PLATAFORMA_OBSERVACIONAL.md`

---

## 1. Princípio

A plataforma separa claramente:

| Camada | Responsabilidade | Tecnologia |
|--------|------------------|------------|
| **Céu / tempo / dados** | Coordenadas, efemérides, tempo, FITS, redução | **Astropy** (+ afiliados) |
| **Serviços web astronômicos** | NEOs, Horizons, MPC, SIMBAD, etc. | **Astroquery** |
| **Hardware do observatório** | Montagem, câmera (via ASCOM), focuser, roda, cúpula… | **ASCOM Alpaca** via **Alpyca** |
| **Hardware SBIG legado** | Câmeras ST USB já suportadas | **Universal Driver** (ctypes) — mantido |
| **Meteorologia do site** | Condições/previsão no local de observação | **Open-Meteo** (hourly) + **RainViewer** (radar PNG) + **ObservingConditions** (Alpaca, depois) + entrada manual |
| **UI / app** | Interface e orquestração | **SaaS:** Next.js · **Desktop:** PySide6 + PyInstaller (`.exe` Windows) · Python ≥ 3.10 |
| **Persistência** | Todo resultado observacional | **BDaaS:** PostgreSQL + object storage · Desktop: SQLite local |

Fluxo típico:

```
Astroquery / catálogo  →  Astropy (SkyCoord, Time, AltAz)
Meteo do Site          →  viabilidade do programa diário
                              ↓
                     Programa diário (alvos + equipamento)
                              ↓
                     Alpyca / udrv → montagem / câmera / focuser
                              ↓
                     Registro FITS + meteo + análise (Astropy)
                              ↓
                     Persistência em BD(s) + artefatos em disco
```

---

## 2. Astropy — arcabouço astronômico

**Papel:** única fonte de verdade para tempo, coordenadas, unidades e I/O FITS.

### Usos obrigatórios na plataforma

| Capacidade | API típica | Onde entra |
|------------|------------|------------|
| Tempo civil / sideral / JD | `astropy.time.Time` | Log de sessão, headers, timing de ocultações |
| Coordenadas equatorias / horizontais | `SkyCoord`, `AltAz`, `EarthLocation` | Planner, slew, visibilidade |
| Transformações de frame | ICRS ↔ AltAz, precessão, etc. | Apontamento e efemérides locais |
| Unidades | `astropy.units` | Evitar bugs de hora/grau |
| FITS | `astropy.io.fits` | Já usado no sbig-suite |
| Tabelas / WCS | `Table`, `wcs` | Fotometria, astrometria |

### O que Astropy não faz sozinho

- Não controla telescópio/câmera → Alpyca/Alpaca (ou udrv SBIG).
- Não baixa efemérides de NEO/Horizons no core → **Astroquery**.

---

## 3. Astroquery — efemérides e serviços

**Papel:** ponte oficial do ecossistema Astropy para serviços remotos.

| Necessidade cidadã | Módulo (exemplos) | Uso |
|--------------------|-------------------|-----|
| Efemérides NEOs / asteroides / cometas | `astroquery.jplhorizons` | Planner NEO, tracking |
| Objetos menores / MPC | `astroquery.mpc` | Follow-up |
| Nomes / coordenadas | `astroquery.simbad` | Resolver alvos |
| Catálogos | Vizier / Gaia | Comparação fotométrica |

### Ocultações

Não há `Astropy.occultations` no core. Estratégia:

1. Efemérides do corpo (Horizons) + estrela (SIMBAD/Gaia) com Astropy/Astroquery.
2. Predição de eventos via ferramentas IOTA (Occult, OccultWatcher, feeds) — importar previsões.
3. Plataforma: carregar previsão → apontar → adquirir com timestamp confiável → reduzir contato.

---

## 4. ASCOM Alpaca + Alpyca — controle de hardware

**Papel:** controle multiplataforma (Windows, Linux, macOS) via HTTP/JSON.

| Item | Decisão |
|------|---------|
| Protocolo | **ASCOM Alpaca** |
| Cliente Python | **Alpyca** (`pip install alpyca`) — docs: https://ascom-standards.org/alpyca/ |
| Documentação local | Espelho completo em [ascom/README.md](ascom/README.md) (interfaces, API Alpaca, newdocs) |
| Mapeamento hardware | [ascom/MAPEAMENTO_EQUIPAMENTO_ASCOM.md](ascom/MAPEAMENTO_EQUIPAMENTO_ASCOM.md) |
| Alternativa Windows-only | COM + `pywin32` — **não preferida** |
| Servidor Windows | ASCOM Platform + ASCOM Remote |
| Dev sem hardware | Alpaca Omni Simulators |

### Dispositivos-alvo

| Prioridade | Dispositivo | Classe Alpyca |
|------------|-------------|---------------|
| P1 | Telescope (montagem) | `Telescope` |
| P1 | Camera | `Camera` |
| P1 | Focuser | `Focuser` |
| P2 | FilterWheel | `FilterWheel` |
| P2 | ObservingConditions | `ObservingConditions` |
| P3 | Dome / Switch / SafetyMonitor | … |

### Integração com sbig-suite

```
CameraBackend
├── UdrvBackend           ← SBIG ST USB (já existe)
├── SimulatorBackend      ← já existe
└── AlpacaCameraBackend   ← NOVO

MountBackend (novo)
├── AlpacaTelescopeBackend
└── SimulatorMountBackend
```

**Regra:** UI e domínio não importam Alpyca/udrv diretamente — só abstrações.

---

## 5. Fluxo de referência (Astropy → Alpyca)

```python
from astropy.coordinates import SkyCoord, EarthLocation, AltAz
from astropy.time import Time
import astropy.units as u

loc = EarthLocation(lat=..., lon=..., height=...)
now = Time.now()
target = SkyCoord.from_name("Polaris")  # ou Astroquery/Horizons
altaz = target.transform_to(AltAz(obstime=now, location=loc))
# validar altitude; depois MountBackend.slew(ra, dec)
```

1. **Astropy** decide para onde e se é observável.  
2. **Alpyca** executa slew / expose / focus.  
3. **FITS** registra pedido + telemetria do hardware.

---

## 6. Pacotes candidatos

| Pacote | Uso | Fase |
|--------|-----|------|
| `astropy` | Já no projeto | Agora |
| `astroquery` | Efemérides / SIMBAD / MPC | P1 |
| `alpyca` | Hardware ASCOM | P1→P2 |
| `photutils` | Fotometria | P2 |
| `specutils` | Espectros 1D | P3 |
| `pyqtgraph` / matplotlib | Plots | P1–P2 |
| INDI | Alternativa Linux | Avaliar depois |

---

## 7. Decisões fechadas

1. Astropy + ASCOM via **Alpaca/Alpyca** (não COM como caminho principal).  
2. **Astroquery** para NEOs/efemérides/serviços.  
3. **udrv SBIG** e **Alpaca Camera** são backends de câmera de primeira classe (escolha na sessão).  
4. **Linux e Windows** com paridade de produto; CI nos dois.  
5. **Montagens diversas** via Alpaca Telescope (agnóstico de marca).  
6. **Focuser** no escopo do produto.  
7. **Site por local de observação** (perfis configuráveis), não coordenada fixa.  
8. Não depender de `pywin32`/COM no código da plataforma (por enquanto).  
9. **Stack de plataforma** alinhada ao motorsport-agent (**D-009**): FastAPI + Next.js + PostgreSQL BDaaS.  
10. **Desktop:** **PySide6 + Python** (D-009.4-rev); Tauri opcional futuro — ver [COMPARACAO_DESKTOP_TAURI_VS_PYSIDE.md](COMPARACAO_DESKTOP_TAURI_VS_PYSIDE.md).  
11. Produção SaaS: **BDaaS** (Postgres + object storage); semi-estruturado via **JSONB**; séries via **Parquet** (faseado).  
12. **Executável Windows:** entrega Desktop exige `.exe` empacotado (PyInstaller) + smoke CI — utilizador final sem Python instalado (AC-075, AC-076).

---

## 7.1 Stack de plataforma (SaaS + Desktop) — D-009

| Camada | Tecnologia | Origem |
|--------|------------|--------|
| API SaaS | FastAPI, Pydantic v2, SQLAlchemy 2, Alembic | motorsport-api |
| Web SaaS | Next.js, React, TypeScript, Tailwind | motorsport-dashboard |
| Desktop | **PySide6** + sync HTTP/SQLite + PyInstaller → `.exe` | sbig-suite + D-009.4-rev |
| Observatory runtime | Mesmo processo Python (Alpyca, udrv, Astropy) | in-process |
| BD mestre | PostgreSQL **BDaaS** | motorsport DBaaS |
| Artefatos | Object storage **BDaaS** (S3-compatível) | evolução motorsport storage |
| Semi-estruturado | JSONB no Postgres | — |
| Séries | Parquet no object store (faseado) | proposta motorsport Parquet |

Detalhe: [AVALIACAO_STACK_MOTORSPORT.md](AVALIACAO_STACK_MOTORSPORT.md) · [COMPARACAO_DESKTOP_TAURI_VS_PYSIDE.md](COMPARACAO_DESKTOP_TAURI_VS_PYSIDE.md) · ADR: [decisoes/D-009-stack-motorsport-bdaas.md](decisoes/D-009-stack-motorsport-bdaas.md) · [decisoes/D-009.4-rev-desktop-pyside.md](decisoes/D-009.4-rev-desktop-pyside.md).

---

## 8. Decisões de campo (fechadas 2026-07-20)

| # | Pergunta | Decisão |
|---|----------|---------|
| 1 | Montagens | **Diversas** — a plataforma não se amarra a um modelo. Controle via interface ASCOM `Telescope` (qualquer driver Alpaca compatível: Celestron, Meade/LX200, EQMOD, etc.). |
| 2 | Sistemas operacionais | **Linux e Windows** (paridade). Cliente Alpyca + Astropy nos dois. No Windows, drivers clássicos via ASCOM Platform + ASCOM Remote (Alpaca). No Linux, dispositivos Alpaca nativos e/ou Remote em outra máquina. |
| 3 | Câmeras | **As duas vias:** (a) **UdrvBackend** para SBIG ST USB; (b) **AlpacaCameraBackend** para qualquer câmera ASCOM. O usuário escolhe o backend na sessão. |
| 4 | Focuser | **Sim** — `FocuserBackend` / Alpyca `Focuser` no escopo (P2, junto com montagem). |
| 5 | Local do observatório | **Por local de observação** — `EarthLocation` configurável por site/sessão (lat, lon, altitude, nome). Sem coordenada hardcoded; perfis de site (ex.: Gramadão, campo, campus) gravados pelo usuário. |

### Implicações de desenho

- **MountBackend** genérico (Alpaca Telescope) + simulador — sem drivers por marca no código da plataforma.
- **CI:** testes em Linux e Windows; Omni Simulators + SimulatorBackend.
- **Camera:** factory/config com `udrv | alpaca | simulator`.
- **SiteProfile:** entidade de domínio (`name`, `lat`, `lon`, `height`, fuso/opcional) usada por planner, FITS headers e conversões AltAz.
- Focuser deixa de ser “opcional se houver hardware” e passa a **requisito de produto**.

---

## 9. Backlog derivado

| ID | Item |
|----|------|
| TECH-01 | Contratos `MountBackend` / estender câmera |
| TECH-02 | PoC Alpyca + Omni Simulator |
| TECH-03 | Serviço planning (Astropy AltAz + site) |
| TECH-04 | Wrapper Astroquery (Horizons/MPC/SIMBAD) |
| TECH-05 | `AlpacaCameraBackend` |
| TECH-06 | FITS com site/tempo/alvo (Astropy) |
| TECH-07 | Política de rede Alpaca (localhost vs remoto) |
| TECH-08 | `SiteProfile` (lat/lon/alt por local de observação) |
| TECH-09 | `FocuserBackend` + Alpyca Focuser |
| TECH-10 | Factory de câmera: udrv \| alpaca \| simulator |

---

## 10. Referências

- https://ascom-standards.org/alpyca/  
- https://ascom-standards.org/Developer/Alpaca.htm  
- https://docs.astropy.org/  
- https://astroquery.readthedocs.io/  
- “ASCOM Alpaca with Bob Denny” (The Astro Imaging Channel)
