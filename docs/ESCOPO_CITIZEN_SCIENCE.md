# Escopo — Astronomia observacional de citizen science

**Mandato científico:** cobre **todas** as áreas da astronomia observacional de citizen science (pequenos telescópios e pequenos observatórios).
**Operação de negócio:** efemérides, meteo do site, programa diário, planejamento de observações/equipamento, registro/análise e gestão de programas — ver `ESCOPO_GERAL_E_REGRAS_DE_NEGOCIO.md`.
**Áreas observacionais oficiais:** templates PO-* em `PROGRAMAS_OBSERVACIONAIS.md` (decisão 2026-07-20).  
**Decisão:** 2026-07-20  
**Entrega:** faseada · **Escopo-alvo:** completo (não opcional)  
**Fontes:** `REVISAO_ASTRONOMIA_OBSERVACIONAL.md`, literatura anexada, redes cidadãs estabelecidas

## 1. Princípio

| Conceito | Significado |
|----------|-------------|
| **Escopo-alvo** | União de todas as áreas abaixo — a plataforma “completa” exige cobertura de cada uma |
| **Roadmap** | Ordem e ritmo de implementação (Tiers / Pn) |
| **Fora de escopo** | Só o explicitamente listado na §4 (teoria pura, CAD de obra, etc.) |

Nenhuma área da §2 pode ser removida do produto sem decisão documentada de exclusão.

---

## 2. Inventário completo (em escopo)

### 2.1 Fundação operacional

| ID | Área | Redes / padrão | Status planejamento |
|----|------|----------------|---------------------|
| CS-F1 | Aquisição CCD/CMOS (udrv SBIG + Alpaca Camera) | FITS | Baseline parcial |
| CS-F2 | Calibração bias/dark/flat | Boas práticas AAVSO/CCD | Planejado |
| CS-F3 | Visualização / inspeção FITS | — | Planejado |
| CS-F4 | Processamento (stack, align) | — | Parcial |
| CS-F5 | Arquivo e metadados de sessão | — | Planejado |
| CS-F6 | Planejamento de noite (Astropy + site) | — | Planejado |
| CS-F7 | Sequenciador de observação | — | Planejado |
| CS-F8 | Foco / seeing / qualidade de imagem | — | Planejado |
| CS-F9 | Catálogos e identificação de alvos | SIMBAD, Vizier, UCAC… | Planejado |
| CS-F10 | Efemérides observacionais (Alt/Az, eventos) | Astropy / Astroquery | Planejado |
| CS-F11 | Meteorologia do local de observação | API meteo / ObservingConditions | Planejado |
| CS-F12 | Programa observacional diário | — | Planejado |
| CS-F13 | Planejamento de equipamento | Inventário + validação | Planejado |
| CS-F14 | Gestão de programas observacionais (campanhas) | AAVSO, MPC, IOTA, ARAS… | Planejado |

### 2.2 Fotometria e séries temporais

| ID | Área | Redes | Status |
|----|------|-------|--------|
| CS-P1 | Fotometria de abertura | — | Planejado |
| CS-P2 | Fotometria diferencial | — | Planejado |
| CS-P3 | Estrelas variáveis | **AAVSO** | Planejado |
| CS-P4 | Multi-filtro (UBVRI / índices de cor) | AAVSO | Planejado |
| CS-P5 | Fotometria rápida / alta cadência | — | Planejado |
| CS-P6 | Trânsitos de exoplanetas | ExoClock / TESS follow-up etc. | Planejado |
| CS-P7 | Microlensing | **µFUN** / alertas | Planejado |
| CS-P8 | Asterosismologia amadora (quando viável) | — | Planejado (tardio) |

### 2.3 Espectroscopia

| ID | Área | Redes | Status |
|----|------|-------|--------|
| CS-S1 | Espectroscopia slit amadora (extração 1D) | — | Planejado |
| CS-S2 | Calibração em comprimento de onda | — | Planejado |
| CS-S3 | Medidas de linhas / classificação | — | Planejado |
| CS-S4 | Monitoramento Be / eruptivas | **ARAS / BeSS** | Planejado |
| CS-S5 | RV educacional / apoio a exoplanetas | — | Planejado |
| CS-S6 | Perfis de instrumento (Lhires, Alpy, DSS-7…) | — | Planejado |
| CS-S7 | Espectroscopia solar amadora | — | Planejado |
| CS-S8 | Echelle amador (quando aplicável) | — | Planejado (tardio) |

### 2.4 Astrometria e alertas do Sistema Solar / transientes

| ID | Área | Redes | Status |
|----|------|-------|--------|
| CS-A1 | Astrometria / plate-solving / WCS | — | Planejado |
| CS-A2 | Asteroides / NEOs | **MPC** | Planejado |
| CS-A3 | Cometas (astrometria / fotometria) | MPC | Planejado |
| CS-A4 | Busca / follow-up de supernovas (blink) | Redes SN / TNS (export) | Planejado |
| CS-A5 | Ocultações | **IOTA** | Planejado |
| CS-A6 | Estrelas duplas (medidas) | — | Planejado |
| CS-A7 | Speckle / alta resolução amadora | — | Planejado (tardio) |

### 2.5 Imaging e observação

| ID | Área | Status |
|----|------|--------|
| CS-I1 | Lua e planetas (lucky imaging / webcam) | Planejado |
| CS-I2 | Deep-sky imaging | Planejado |
| CS-I3 | Sol (observação/imagem **segura**) | Planejado |
| CS-I4 | Diário de observação visual (opcional no mesmo app) | Planejado |

### 2.6 Hardware e observatório

| ID | Área | Status |
|----|------|--------|
| CS-H1 | Montagens diversas (Alpaca Telescope) | Planejado |
| CS-H2 | Câmeras SBIG udrv + ASCOM Alpaca | Planejado / parcial udrv |
| CS-H3 | Focuser | Planejado |
| CS-H4 | Roda de filtros | Parcial (CFW udrv) |
| CS-H5 | Autoguia / AO | Parcial |
| CS-H6 | Condições ambientais (ObservingConditions) | Planejado |
| CS-H7 | Cúpula / switches / safety | Planejado (tardio) |
| CS-H8 | Site por local de observação (`SiteProfile`) | Planejado |
| CS-H9 | Observatório remoto / automação de sessão | Planejado |

### 2.7 Rádio-astronomia cidadã

| ID | Área | Status |
|----|------|--------|
| CS-R1 | Recepção educacional (ex.: 21 cm / VHF / Sol em rádio) | Planejado (eixo paralelo) |
| CS-R2 | Aquisição + plot / arquivo de séries de potência | Planejado |

### 2.8 Polarimetria e nichos

| ID | Área | Status |
|----|------|--------|
| CS-N1 | Polarimetria amadora | Planejado (tardio) |
| CS-N2 | Outros programas cidadãos emergentes | Inclusão por extensão documentada |

### 2.9 Educação e contribuição

| ID | Área | Status |
|----|------|--------|
| CS-E1 | Roteiros de laboratório / sessão guiada | Planejado |
| CS-E2 | Export e validação para redes cidadãs | Planejado |
| CS-E3 | Treino com simuladores (sem hardware) | Parcial |

---

## 3. Ordem de entrega (não reduz escopo)

A ordem segue os Tiers da revisão de domínio e o backlog P0–P5 / TECH.  
**Completo** = §2 inteira satisfeita conforme critérios em `PLATAFORMA_OBSERVACIONAL.md` §8.1.

Sugestão de ondas:

1. Fundação + hardware (câmera, montagem, focuser, site)  
2. Fotometria + variáveis + AAVSO  
3. Espectroscopia slit + ARAS  
4. Astrometria + NEO/MPC + SN blink  
5. Ocultações IOTA + trânsitos  
6. Imaging lunar/planetário/deep-sky + solar  
7. Microlensing + fotometria rápida  
8. Cúpula/remoto + polarimetria + echelle  
9. Rádio cidadão  

---

## 4. Explicitamente fora de escopo (software)

- Astrofísica teórica como produto (cursos de cosmologia, QM, etc.)
- CAD / engenharia civil de observatório
- Conteúdo de revistas como feature
- Redistribuição de drivers proprietários (SBIG udrv)
- Substituição total de ferramentas especializadas externas quando a integração for melhor (ex.: OccultWatcher) — a plataforma **integra/importa**, não precisa clonar 100% de cada app legado

---

## 5. Redes cidadãs a interoperar (mínimo)

| Rede | Domínio |
|------|---------|
| AAVSO | Variáveis / fotometria |
| MPC | Astrometria de objetos menores |
| IOTA | Ocultações |
| ARAS / BeSS | Espectroscopia estelar |
| µFUN (e similares) | Microlensing |
| ExoClock / projetos de trânsito | Exoplanetas |
| Redes de SN / TNS (export) | Transientes |

---

## 6. Rastreabilidade

Cada item CS-* deve, no tempo, ter:

- entrada no `BACKLOG.md` (ou épico ligado),
- workflow em `WORKFLOWS.md` (quando existir),
- critério de aceite testável (dados reais ou simulador).
