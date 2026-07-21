# Revisão da literatura — Áreas da astronomia observacional

**Fontes:**  
- `/media/mminozzo/OBERON1/literatura/Astronomia`  
- `/media/mminozzo/OBERON1/Espectrografia astronomica`  

**Foco:** astronomia observacional **cidadã**, **pequenos telescópios** e **pequenos observatórios** (clubes, escolas, campus, amadores avançados).  

**Status:** revisão de domínio (sem implementação de software)  
**Data:** 2026-07-20  
**Stack tecnológica:** ver `STACK_TECNOLOGICA.md` (Astropy + Alpyca/Alpaca + Astroquery)

---

## 1. O que a coleção é (e o que não é)

A biblioteca é um **arquivo pessoal de formação e prática observacional**, acumulado ao longo de anos. Mistura:

| Camada | Exemplos | Uso para um projeto de plataforma |
|--------|----------|-----------------------------------|
| **Operacional / prática** | CCD, SBIG/ST-7, fotometria, espectroscopia amadora, IOTA, Astrometrica, IRAF, construção de observatório, automação | **Alta** — define requisitos reais |
| **Programas científicos cidadãos** | variáveis, supernovas, NEOs, ocultações, exoplanetas/Microlensing (µFUN), ARAS/Be stars, solar | **Alta** — define *o que* observar e entregar |
| **Instrumentação & óptica** | telescópios, espelhos, Lhires, design de espectrógrafo, Alt-Az, Celestron/Meade/LX200 | **Média–alta** — define hardware alvo |
| **Teoria / astrofísica** | cosmologia, mecânica, stellar astrophysics, 100+ livros Springer | **Baixa para produto** — suporte à interpretação |
| **Divulgação / revistas** | Sky & Telescope, Astronomy Magazine, vídeos, palestras IF/CRT | **Baixa** — inspiração e educação |

**Conclusão:** o material justifica uma plataforma centrada em **observar → calibrar → medir → contribuir**, não um livro-texto interativo de astrofísica.

---

## 2. Ecossistema típico coberto pela literatura

O material descreve o ciclo de vida de um **pequeno observatório / telescópio cidadão**:

```
Planejar noite → Apontar/guiar → Adquirir (CCD/DSLR/webcam)
       → Calibrar (bias/dark/flat) → Reduzir/medir
       → Arquivar → Reportar (AAVSO, IOTA, MPC, ARAS, …)
```

Hardware recorrente no acervo: **SBIG ST-7/ST-8**, DSI Pro, Atik, Celestron CG5/Advanced GT, Meade/LX200, Autostar, espectrógrafos **Lhires III / Alpy**, dados reais do **Gramadão**.

Contexto institucional/local: projetos **CASF**, **Bauru**, **CRT**, cursos **IFSP**, **TAOA**, observações solares e deep-sky próprias.

---

## 3. Mapa completo das áreas importantes

Cada área abaixo aparece de forma **explícita** na literatura anexada, é **viável** com telescópios/pequenos observatórios, e é candidata a módulo numa plataforma de astronomia cidadã.

Legenda de **potencial cidadão**: ★★★ núcleo / ★★ forte / ★ possível mas niche.

### A. Fundação observacional (infraestrutura comum)

| # | Área | Evidência na literatura | Potencial | Produto típico |
|---|------|-------------------------|-----------|----------------|
| A1 | Aquisição CCD/CMOS | `ST-7/`, `PRATICAS CCD/`, Gramadão SBIG | ★★★ | Controle de câmera, FITS |
| A2 | Calibração de imagem | Práticas CCD, bias/dark Gramadão | ★★★ | Pipeline de redução |
| A3 | Visualização FITS | Apostila DS9, Blink Tutorial | ★★★ | Viewer tipo DS9 |
| A4 | Processamento de imagem | Digital Astrophotography, `imagens tratamento/` | ★★★ | Stack / align |
| A5 | Metadados e arquivo | fits_standard, checklists | ★★★ | Arquivo + log |
| A6 | Planejamento de noite | Astronomy with a Home Computer, Practical Astronomy… | ★★★ | Planner / sequenciador |
| A7 | Foco, seeing, qualidade | `FWHM médio/`, dicas de foco IFSP | ★★ | Seeing / foco |
| A8 | Catálogos e identificação | UCAC4, atlases, GCVS | ★★★ | Overlay WCS / ID |

### B. Fotometria e monitoramento temporal

| # | Área | Potencial | Notas |
|---|------|-----------|-------|
| B1–B3 | Abertura, diferencial, variáveis | ★★★ | AAVSO |
| B4 | Multi-filtro UBVRI | ★★ | Clusters |
| B5 | Fotometria rápida | ★★ | `fast fotometro/` |
| B6 | Trânsitos de exoplanetas | ★★★ | `extrasolares/` |
| B7 | Microlensing | ★★ | `microfun/` |
| B8 | Asterosismologia amadora | ★ | Avançado |

### C. Espectroscopia

| # | Área | Potencial | Notas |
|---|------|-----------|-------|
| C1–C4 | Slit amadora, λ-calib, linhas, ARAS/Be | ★★★ | Dir. Espectrografia + Lhires/ISIS |
| C5 | RV educacional / exoplanetas | ★★ | 51 Peg b |
| C6 | Design de espectrógrafo | ★★ | Calculadora |
| C7–C8 | Solar espectral / echelle | ★–★★ | Extensões |

### D. Astrometria, Sistema Solar e alertas

| # | Área | Potencial |
|---|------|-----------|
| D1 | Astrometria / plate-solving | ★★★ |
| D2 | Asteroides / NEOs | ★★★ |
| D3 | Supernovas (blink) | ★★★ |
| D4 | Ocultações IOTA | ★★★ |
| D5–D6 | Cometas / duplas | ★★ |
| D7 | Speckle (avançado) | ★ |

### E. Imaging (Lua, planetas, Sol, deep-sky)

E1 lunar/planetário ★★★ · E2 solar ★★★ · E3 deep-sky ★★★ · E4 visual/binóculos ★★

### F. Rádio-astronomia amadora

Coleção muito grande (`radioastronomy/` ~133 docs). Tratar como **produto irmão** (backend próprio), não plug-in do fluxo CCD.

### G. Instrumentação e observatório

G1 montagens GoTo ★★★ · G2 autoguia/AO ★★★ · G3 automação ★★ · G4 site/construção ★ (docs) · G5–G8 ATM, manutenção, polarimetria, buyer guides

### H. Educação e ciência cidadã

Labs CCD, redes AAVSO/IOTA/ARAS/MPC/µFUN, checklists operacionais, divulgação.

### I. Teoria (contexto, não MVP de software)

Evolução estelar, cosmologia, mecânica, etc.

---

## 4. Prioridade de *entrega* (escopo-alvo = tudo que é citizen science)

**Mandato de produto:** cobrir **todas** as áreas observacionais de citizen science — ver `ESCOPO_CITIZEN_SCIENCE.md`.  
Os Tiers abaixo são só a **ordem de implementação**, não exclusões.

**Tier 1 (primeiro):** aquisição+calibração → planner → fotometria/variáveis → espectroscopia slit → astrometria/blink  

**Tier 2:** ocultações, trânsitos, imaging, solar, montagem (Alpaca), focuser, export para redes  

**Tier 3:** microlensing, fotometria rápida, remoto/cúpula, rádio cidadão, polarimetria, echelle  

**Fora do software (não é “Tier 4 de produto”):** obra civil, ATM de espelhos, revistas, teoria pura  

---

## 5. Programas científicos cidadãos no acervo

Variáveis (AAVSO) · Supernovas · NEOs/MPC · Ocultações/IOTA · ARAS/Be · Trânsitos · Microlensing µFUN · Solar · Rádio · Deep-sky/educação (Gramadão, CRT/IFSP)

---

## 6. Lacunas do acervo (não assumir cobertura total)

CMOS/ZWO moderno, echelle amador hands-on, Siril/PixInsight contemporâneos, INDI unificado — entram como extensão de mercado, não como requisito da literatura.

---

## 7. Implicações para a plataforma

1. Núcleo óptico CCD (onde o sbig-suite começa)  
2. Módulos de medida: fotometria, espectroscopia, astrometria  
3. Programas: variáveis, SN/NEO, ocultações, trânsitos, ARAS  
4. Operação: planner, sequenciador, montagem Alpaca, (depois) cúpula  
5. Eixo paralelo: rádio educacional  
6. Camada educacional: labs IFSP/TAOA  

---

## 8. Matriz rápida

| Área | Evidência | Prioridade |
|------|-----------|------------|
| CCD / calibração / FITS | Muito forte | P0 |
| Fotometria / variáveis | Forte | P1 |
| Espectroscopia amadora | Muito forte | P1 |
| Astrometria / NEO / SN | Forte | P1–P2 |
| Ocultações IOTA | Forte | P2 |
| Exoplanetas | Médio–forte | P2 |
| Imaging / solar | Forte / médio | P2 |
| Montagem (Alpaca) | Médio | P1–P2 (stack) |
| Rádio amador | Muito forte (volume) | Paralelo |
| Teoria | Muito forte (volume) | Fora do MVP |

---

## 9. Stack tecnológica (complemento)

Decisões — ver **`STACK_TECNOLOGICA.md`**:

- **Astropy** — tempo, coordenadas, FITS, redução  
- **Astroquery** — Horizons / MPC / SIMBAD (NEOs, efemérides)  
- **ASCOM Alpaca + Alpyca** — montagem, câmera ASCOM, focuser…  
- **Universal Driver SBIG** — mantido para ST USB  

Ocultações: Horizons/SIMBAD + previsões IOTA + timing local (não há serviço “occultation” no core do Astropy).

---

## 10. Próximo uso

1. Validar Tiers no escopo da plataforma.  
2. Cruzar com `PLATAFORMA_OBSERVACIONAL.md`.  
3. Escolher 2–3 programas âncora.  
4. Responder perguntas abertas da stack (montagem, OS, site).

---

## Apêndice — pastas temáticas mais relevantes

| Pasta | Papel |
|-------|--------|
| `PRATICAS CCD/`, `material CCD/`, `ST-7/`, `Astronomia Gramadão SBIG/` | Núcleo CCD/SBIG |
| `espectroscopia/` + `Espectrografia astronomica` | Espectroscopia |
| `fotometria/`, `estrelas variaveis/` | Fotometria |
| `astrometrica/`, `NEO/`, `busca de supernovas/` | Astrometria / alertas |
| `OCULTACOES/`, `Ocultaçoes/`, `IOTA 2010…` | Ocultações |
| `extrasolares/`, `Extrasolar Planets/`, `microfun/` | Exoplanetas |
| `solar/`, `observacoes sol/`, `Sol/` | Solar |
| `Radioastronomia/`, `radioastronomy/` | Rádio |
| `telescopio automação/`, `treinamento TAOA/` | Automação |
| `Observatorio/`, `construcao observatorio/`, `CRT/` | Site / projetos locais |
| `20 Astronomy eBooks Pack/`, `astro-literatura/` | Prática amadora |
| `IRAF/`, `processamento de imagens/` | Redução |
| `polarimetria/`, `fast fotometro/` | Nichos avançados |
| `Astrophysics (103 books)/`, cosmologia | Teoria (contexto) |
