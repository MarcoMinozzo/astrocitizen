# Índice curado de literatura → módulos

**Status:** Rascunho Fase 0  
**Objetivo:** Ligar obras dos diretórios anexos às capacidades da plataforma.  
**Não é** catálogo completo da biblioteca — só o que informa requisitos de software.

---

## Caminhos-raiz

- A = `/media/mminozzo/OBERON1/literatura/Astronomia`
- E = `/media/mminozzo/OBERON1/Espectrografia astronomica`

---

## Aquisição / CCD / calibração → Fundação (P0)

| Obra / pasta | Path | Informa |
|--------------|------|---------|
| Dados reais Gramadão (FITS/ST8) | `A/Astronomia Gramadão SBIG/` | Corpus de testes, masters |
| Manuais / legado ST-7 + CCDOPS | `A/ST-7/` | Paridade com fluxos clássicos |
| Práticas CCD / labs | `A/PRATICAS CCD/` | Workflows didáticos e astrometria |
| *A practice guide of CCD* | `A/` | Boas práticas CCD |
| AAVSO CCD Manual | `A/` (várias cópias) | Padrões de calibração e fotometria |
| *fits_standard* | `A/` | Conformidade FITS |
| Apostila DS9 | `A/Apostila_DS9_PAE.pdf` | Requisitos do visualizador |

## Espectroscopia → P3

| Obra | Path | Informa |
|------|------|---------|
| *Astronomical Spectroscopy for Amateurs* | `E/` e `A/` | Fluxo amador completo |
| Tennyson — *Astronomical Spectroscopy* | `E/` | Física / interpretação |
| Massey & Hanson | `E/` e `A/espectroscopia/` | Técnicas observacionais |
| *Spectrograph design fundamentals* | `E/` | Modelo do instrumento |
| Schroeder — *Astronomical optics* | `E/` | Óptica do espectrógrafo |
| Robinson — *Key to the Stars* | `E/` | Leitura de linhas |
| Andor — Echelle learning | `E/` | Contexto echelle (avançado) |
| Buil ISIS / Alpy tutorial | `A/` | Pipeline prático de redução |
| Lhires III User Guide | `A/DC0004A_-_Lhires_III_…` | Perfil de instrumento |
| Pasta `espectroscopia` + ARAS | `A/espectroscopia/` | Casos Be / eruptivas |
| 51 Peg b espectroscopia | `A/` | Caso exoplaneta / RV |

## Fotometria / variáveis → P2

| Obra / pasta | Path | Informa |
|--------------|------|---------|
| Pasta fotometria | `A/fotometria/` | Métodos e exemplos |
| Young Photometry | `A/` | Referência técnica |
| Estrelas variáveis | `A/estrelas variaveis/` | Tipos e motivação de campanhas |
| Algoritmos centroide / CCD photometry | `A/estrelas variaveis/`, `A/PRATICAS CCD/` | Implementação |

## Astrometria / NEO / supernovas / ocultações → P4

| Obra / pasta | Path | Informa |
|--------------|------|---------|
| Astrometrica / práticas | `A/astrometrica/`, `A/PRATICAS CCD/` | Plate-solve, catálogos |
| Blink / busca supernovas | `A/busca de supernovas/` | Diff imaging |
| IOTA / ocultações | `A/OCULTACOES/`, `A/Ocultaçoes/` | Timing |
| UCAC4 / NEO | `A/ucac4/`, `A/NEO/` | Catálogos / follow-up |

## Sessão / observatório → P1 / P5

| Obra / pasta | Path | Informa |
|--------------|------|---------|
| *Astronomy with a Home Computer* | `A/20 Astronomy eBooks Pack/` | Planejamento |
| *Practical Astronomy… Spreadsheet* | `A/` | Efemérides / utilitários |
| *Building a Roll-Off Roof Observatory* | `A/` | Contexto operacional |
| Automação telescópio / Gemini Net | `A/telescopio automação/`, `A/automação observatorio/` | Integração futura |
| Projetos observatório (CASF, Bauru, etc.) | `A/Observatorio/` | Requisitos locais históricos |

## Processamento de imagem → P0 / viewer

| Obra / pasta | Path | Informa |
|--------------|------|---------|
| *Creating and Enhancing Digital Astro Images* | `A/` / eBooks Pack | Redução estética vs. científica |
| *Digital Astrophotography* | `A/` | Estado da arte amador |
| IRAF beginners | `A/IRAF/` | Referência clássica de redução |
| Pasta imagens tratamento | `A/imagens tratamento/` | Exemplos locais |

## Baixa prioridade para requisitos de software

Revistas (*Sky & Telescope*, *Astronomy*), coleções teóricas grandes de astrofísica, vídeos de palestras, material histórico — úteis para contexto científico, **não** geram épicos de produto na Fase 0–4.

---

## Próximo refinamento sugerido

Para cada item P0–P3 do `BACKLOG.md`, anotar 1–3 páginas/capítulos concretos das obras acima como “spec científica” do requisito.
