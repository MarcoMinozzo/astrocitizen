# Programas observacionais possíveis — classificação a partir da literatura

**Fontes:**  
`/media/mminozzo/OBERON1/literatura/Astronomia` · `/media/mminozzo/OBERON1/Espectrografia astronomica`  

**Status:** **DECISÃO DE PRODUTO (2026-07-20)** — estas são as **áreas / programas observacionais oficiais** da plataforma.  
**Uso:** catálogo canônico de **ProgramasObservacionais** (templates PO-*). Ver `ESCOPO_GERAL_E_REGRAS_DE_NEGOCIO.md`.  
**Data:** 2026-07-20  

> Inclusão, exclusão ou fusão de um PO-* exige decisão documentada. A ordem P1–P4 é apenas de entrega.

---

## Como ler esta classificação

| Dimensão | Significado |
|----------|-------------|
| **Classe** | Família científica / técnica |
| **Evidência** | Força no acervo (★★★ pasta/obras dedicadas · ★★ várias referências · ★ menção/viável) |
| **Rede** | Destino cidadão típico |
| **Técnica** | Método principal de aquisição/análise |
| **Prioridade de produto** | Ordem sugerida de inclusão na plataforma (P1–P4), sem excluir nenhuma do mandato |

Todos os itens abaixo **compõem o escopo observacional oficial** da plataforma; a prioridade P1–P4 é só a ordem de entrega.

---

## A. Fotometria e monitoramento temporal

| ID | Programa | Evidência | Rede | Técnica | Prioridade | Base na literatura |
|----|----------|-----------|------|---------|------------|-------------------|
| PO-A01 | **Estrelas variáveis (geral)** | ★★★ | AAVSO | Fotometria diferencial | P1 | `estrelas variaveis/`, GCVS, AAVSO CCD Manual |
| PO-A02 | **Variáveis eruptivas / cataclísmicas** | ★★ | AAVSO | Fotometria (cadência alta) | P2 | Tipos GCVS; ARAS overlap espectral |
| PO-A03 | **Cefeidas / RR Lyrae (periódicas)** | ★★ | AAVSO | Fotometria multi-noite | P2 | Materiais de variáveis + fotometria |
| PO-A04 | **Fotometria de aglomerados (cores UBVRI)** | ★★ | — / educação | Multi-filtro | P2 | `fotometria/` (Pleiades, Magalhães) |
| PO-A05 | **Trânsitos de exoplanetas** | ★★★ | ExoClock / TESS follow-up | Fotometria de alta precisão | P1 | `extrasolares/`, Detection… Extrasolar Planets, exoplanet observing |
| PO-A06 | **Microlensing** | ★★★ | µFUN | Fotometria densa / alertas | P2 | `microfun/` |
| PO-A07 | **Fotometria rápida / sub-segundo** | ★★ | — | Alta cadência | P3 | `fast fotometro/` |
| PO-A08 | **Asterosismologia amadora** | ★★ | — | Séries temporais longas | P3 | *Asteroseismology*, `asterosismologia*` |
| PO-A09 | **Curvas de luz de asteroides (rotação)** | ★★ | — / MPC aux. | Fotometria + tracking | P2 | NEO + fotometria CCD |
| PO-A10 | **Fotometria de cometas** | ★ | MPC / redes de cometas | Fotometria + não-sideral | P3 | Material Sistema Solar / cometas |

---

## B. Espectroscopia

| ID | Programa | Evidência | Rede | Técnica | Prioridade | Base na literatura |
|----|----------|-----------|------|---------|------------|-------------------|
| PO-B01 | **Espectroscopia estelar geral (slit)** | ★★★ | — / educação | Extração 1D + λ | P1 | *Spectroscopy for Amateurs*, Tennyson, Massey & Hanson, ISIS/Alpy, Lhires |
| PO-B02 | **Estrelas Be / envelopes circumestelares** | ★★★ | ARAS / BeSS | Monitoramento de linhas (Hα…) | P1 | ARAS Eruptive Stars, Be stars, `espectroscopia/` |
| PO-B03 | **Estrelas eruptivas / novae (espectro)** | ★★★ | ARAS | Séries espectrais | P1 | ARAS 2014–2015 |
| PO-B04 | **Classificação espectral (MK)** | ★★ | — / educação | Comparação de templates | P2 | Robinson *Key to the Stars*, Tennyson |
| PO-B05 | **RV / exoplanetas (educacional)** | ★★ | — | Doppler / calibração λ | P2 | 51 Peg b espectroscopia |
| PO-B06 | **Espectroscopia solar** | ★★ | Redes solares | Linhas solares / (intro) Zeeman | P2 | Zeeman/magnetografia solar; `solar/` |
| PO-B07 | **Echelle amador (alta resolução)** | ★ | — | Echelle | P4 | Andor Echelle learning |
| PO-B08 | **Desenvolvimento / calibração de espectrógrafo** | ★★ | — / lab | Flats, lâmpada, resolução | P3 | *Spectrograph design*, Schroeder optics, Design a spectrograph |

---

## C. Astrometria, NEOs e transientes

| ID | Programa | Evidência | Rede | Técnica | Prioridade | Base na literatura |
|----|----------|-----------|------|---------|------------|-------------------|
| PO-C01 | **Astrometria de asteroides / NEOs** | ★★★ | **MPC** | Plate-solve + medidas | P1 | `NEO/`, Astrometrica, UCAC4 |
| PO-C02 | **Follow-up de descoberta NEO** | ★★★ | MPC | Tracking não-sideral | P1 | Programa NEO NASA / apresentações |
| PO-C03 | **Busca / confirmação de supernovas** | ★★★ | Redes SN / TNS | Blink / diff imaging | P1 | `busca de supernovas/`, Blink Tutorial |
| PO-C04 | **Astrometria de cometas** | ★★ | MPC | Tracking não-sideral | P2 | Astrometrica stacking/tracking |
| PO-C05 | **Identificação / recuperação de objetos** | ★★ | MPC | Astrometria + efemérides Horizons | P2 | Horizons + Astrometrica |

---

## D. Ocultações e timing

| ID | Programa | Evidência | Rede | Técnica | Prioridade | Base na literatura |
|----|----------|-----------|------|---------|------------|-------------------|
| PO-D01 | **Ocultações de asteroides (estrelas)** | ★★★ | **IOTA** | Timing de alta precisão | P1 | IOTA Observers Manual, `OCULTACOES/`, Feronia |
| PO-D02 | **Ocultações lunares / grazes** | ★★ | IOTA | Timing / vídeo | P2 | IOTA 2010, Archive of Lunar Grazes |
| PO-D03 | **Ocultações mutuas de satélites (ex.: Io/Europa)** | ★★ | IOTA | Timing | P3 | IOTA 2010 Io/Europa |
| PO-D04 | **Duplas por occultation / vídeo** | ★★ | — / IOTA | Timing + análise | P3 | New Video Method to Measure Double Stars |

---

## E. Sistema Solar — imaging e observação

| ID | Programa | Evidência | Rede | Técnica | Prioridade | Base na literatura |
|----|----------|-----------|------|---------|------------|-------------------|
| PO-E01 | **Lua (imaging / terminador)** | ★★★ | — / educação | Webcam/DSLR + stack | P2 | *Lunar and Planetary Webcam*, Atlas of Lunar Terminator, observações próprias |
| PO-E02 | **Planetas (Júpiter, Saturno, Marte…)** | ★★★ | — / ALPO-like | Lucky imaging | P2 | Lunar and Planetary guides; imagens ST-7 (M57 etc. também deep-sky) |
| PO-E03 | **Sol em luz branca / manchas** | ★★★ | Redes solares amadoras | Imaging seguro | P1 | `solar/`, `observacoes sol/`, `Sol/`, fotografando o sol |
| PO-E04 | **Sol em Hα / atividade** | ★★ | Redes solares | Filtro Hα (se houver) | P2 | Material solar + espectroscopia solar |
| PO-E05 | **Eclipses lunares / solares** | ★★ | — / educação | Timing + imaging | P2 | eclipse lua 2010, eclipse 2010 |
| PO-E06 | **Cometas (imaging)** | ★ | Redes de cometas | Imaging + tracking | P3 | Literatura Sistema Solar |

---

## F. Deep-sky e observação visual

| ID | Programa | Evidência | Rede | Técnica | Prioridade | Base na literatura |
|----|----------|-----------|------|---------|------------|-------------------|
| PO-F01 | **Deep-sky imaging (galáxias, nebulosas, clusters)** | ★★★ | — / educação | CCD/DSLR LRGB | P2 | Andromeda CR2, Gramadão SBIG, *Digital Astrophotography*, *100 Best Targets* |
| PO-F02 | **Catálogo Messier / listas de caça** | ★★★ | — / educação | Visual ou imaging | P2 | Catalogo Messier, Deep-Sky Hunter, Finlay Concise Catalog |
| PO-F03 | **Observação visual (binóculo / ocular)** | ★★★ | — / diário | Log visual | P3 | *Binocular Astronomy*, *Visual Astronomy…*, *1,001 Celestial Wonders* |
| PO-F04 | **Asterismos / reconhecimento de céu** | ★★ | educação | Visual / planner | P3 | *Pattern Asterisms*, Night Sky Companion |

---

## G. Estrelas duplas e alta resolução angular

| ID | Programa | Evidência | Rede | Técnica | Prioridade | Base na literatura |
|----|----------|-----------|------|---------|------------|-------------------|
| PO-G01 | **Medição de estrelas duplas** | ★★★ | WDS / redes de duplas | Imaging / eyepiece micrometer | P2 | *Double Stars for Small Telescopes*, High Delta M Doubles |
| PO-G02 | **Speckle interferometry (avançado)** | ★★ | — | Speckle | P4 | Lowell Speckle Workshop, Horch WIYN |

---

## H. Polarimetria

| ID | Programa | Evidência | Rede | Técnica | Prioridade | Base na literatura |
|----|----------|-----------|------|---------|------------|-------------------|
| PO-H01 | **Polarimetria astronômica amadora/avançada** | ★★ | — | Polarímetro + CCD | P4 | `polarimetria/` (dissertação) |

---

## I. Rádio-astronomia cidadã

| ID | Programa | Evidência | Rede | Técnica | Prioridade | Base na literatura |
|----|----------|-----------|------|---------|------------|-------------------|
| PO-I01 | **Sol em rádio** | ★★★ | Clubes rádio-astro | Potência vs tempo | P3 | Hyde, Smith *Radio Exploration of the Sun*, mini-curso |
| PO-I02 | **Linha de 21 cm (HI)** | ★★★ | Educação / clubes | Espectro/recepção | P3 | `radioastronomy/` (1420 MHz), Goldstone basics |
| PO-I03 | **Continuo / fontes brilhantes (verificação)** | ★★ | Educação | Drift scan / pointing | P3 | Source Verification, DeepSpaceRadioAst |
| PO-I04 | **Radiotelescópio educacional (VHF etc.)** | ★★★ | Educação | Autoconstrução + aquisição | P3 | Autocostruzione radiotelescopio VHF, mini-curso |

---

## J. Qualidade de site, instrumento e calibração (programas de apoio)

Não são “ciência de alvo”, mas são **programas operacionais** gerenciáveis na plataforma.

| ID | Programa | Evidência | Prioridade | Base |
|----|----------|------------|------------|------|
| PO-J01 | **Caracterização de CCD (ganho, ruído, dark)** | ★★★ | P1 | Determinação Experimental do Ruído…, AAVSO CCD, Gramadão bias/dark |
| PO-J02 | **Monitoramento de seeing / FWHM** | ★★ | P2 | `FWHM médio/`, otica ativa |
| PO-J03 | **Campanha de flats/darks mestres (calibração de rotina)** | ★★★ | P1 | PRATICAS CCD, Gramadão |
| PO-J04 | **Teste / colimação / foco** | ★★ | P2 | dicas de foco IFSP, Care of Telescopes |
| PO-J05 | **Meteorologia observacional do site** | ★★ | P1 | Observatorio (clima Ceará), RN meteo |

---

## K. Educação e extensão (programas didáticos)

| ID | Programa | Evidência | Prioridade | Base |
|----|----------|------------|------------|------|
| PO-K01 | **Laboratório CCD / redução de imagens** | ★★★ | P2 | `PRATICAS CCD/`, TAOA, IFSP |
| PO-K02 | **Mini-curso espectroscopia** | ★★★ | P2 | apresentacao_espectroscop, Thizy intro |
| PO-K03 | **Mini-curso rádio** | ★★★ | P3 | mini curso radioastronomia |
| PO-K04 | **Projeto de observatório escolar/campus** | ★★ | P3 | CRT, CASF, Bauru, IAG checklist |

---

## Resumo por classe

| Classe | Qtd. programas | Evidência média | Inclusão |
|--------|----------------|-----------------|----------|
| A Fotometria / tempo | 10 | Alta | Núcleo |
| B Espectroscopia | 8 | Muito alta | Núcleo |
| C Astrometria / NEO / SN | 5 | Alta | Núcleo |
| D Ocultações | 4 | Alta | Núcleo |
| E Sistema Solar imaging | 6 | Alta | Núcleo |
| F Deep-sky / visual | 4 | Alta | Núcleo |
| G Duplas / speckle | 2 | Média | Núcleo / tardio |
| H Polarimetria | 1 | Média | Tardio |
| I Rádio | 4 | Muito alta (volume) | Paralelo |
| J Apoio / calibração / site | 5 | Alta | Fundação |
| K Educação | 4 | Alta | Transversal |
| **Total** | **~53** | | |

---

## Classificação por prioridade de inclusão na plataforma

### P1 — primeira onda de ProgramasObservacionais (templates no produto)

1. PO-A01 Variáveis (AAVSO)  
2. PO-A05 Trânsitos de exoplanetas  
3. PO-B01 Espectroscopia slit geral  
4. PO-B02 / PO-B03 Be e eruptivas (ARAS)  
5. PO-C01 / PO-C02 NEOs / MPC  
6. PO-C03 Supernovas (blink)  
7. PO-D01 Ocultações de asteroides (IOTA)  
8. PO-E03 Sol (manchas / luz branca)  
9. PO-J01 / PO-J03 / PO-J05 Calibração CCD + meteo do site  

### P2 — segunda onda

Variáveis periódicas/eruptivas · clusters UBVRI · microlensing · fotometria de asteroides · classificação espectral · RV educacional · espectroscopia solar · cometas astrométricos · ocultações lunares · Lua/planetas imaging · deep-sky · Messier · duplas · seeing/foco · labs CCD/espectro  

### P3 — terceira onda

Fotometria rápida · asterosismologia · fotometria de cometas · imaging de cometas · eclipses · visual/binóculo · rádio (Sol, 21 cm, continuo, VHF) · design de espectrógrafo · projetos educacionais de observatório  

### P4 — quarta onda (avançado / niche)

Echelle · speckle · polarimetria  

---

## Classificação por técnica dominante

| Técnica | Programas |
|---------|-----------|
| **Fotometria** | A01–A10, parte E05, J02 |
| **Espectroscopia** | B01–B08 |
| **Astrometria / blink** | C01–C05, F01 (apoio WCS) |
| **Timing** | D01–D04, parte E05 |
| **Imaging / lucky** | E01–E06, F01 |
| **Visual** | F02–F04 |
| **Rádio** | I01–I04 |
| **Polarimetria** | H01 |
| **Calibração / meteo** | J01–J05 |
| **Educação (misto)** | K01–K04 |

---

## Classificação por rede cidadã

| Rede | Programas |
|------|-----------|
| **AAVSO** | A01–A04 (e afins) |
| **MPC** | C01–C05, A09/A10 (apoio) |
| **IOTA** | D01–D04 |
| **ARAS / BeSS** | B02–B03 (B01 suporte) |
| **µFUN** | A06 |
| **ExoClock / trânsitos** | A05 |
| **Redes solares** | E03–E04, B06, I01 |
| **WDS / duplas** | G01 |
| **SN / TNS** | C03 |
| **Sem rede (educação/arquivo local)** | F*, K*, J*, parte E/B |

---

## Mapeamento para a plataforma (entidade ProgramaObservacional)

Cada linha PO-* vira um **template de programa** com:

- tipo / classe (A–K)  
- técnica  
- produto mínimo (RN-043)  
- rede(s)  
- requisitos de equipamento  
- limiares de céu/meteo  
- cadência sugerida  

O **ProgramaDiario** agrega blocos vindos de vários PO-* ativos no mesmo Site.

---

## Nota sobre o que *não* vira programa observacional

Livros de cosmologia, mecânica quântica, fluidos, etc. **não** geram PO-* — são contexto teórico.  
Revistas *Sky & Telescope* / *Astronomy* inspiram alvos, mas o programa concreto vem das classes acima.
