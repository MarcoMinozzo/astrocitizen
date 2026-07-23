---
chunk_id: docs-programas-009
source_id: docs-programas
path: docs/PROGRAMAS_OBSERVACIONAIS.md
title: Classificação por técnica dominante
trust_tier: T3
lang: pt
topics: ["programs", "po"]
po_id: null
network: aavso
pipeline_stage: help
token_estimate: 341
chunk_hash: "sha256:072ffce5e279c088ef2e6ca8318e247b0da3c6e0fd151683fa24d81643da5a54"
corpus_version: 0.1.0-kb1
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
