---
chunk_id: docs-entrada-002
source_id: docs-entrada
path: docs/ENTRADA_OBSERVACOES_POR_PO.md
title: 3. Metadados comuns (todos os PO-*)
trust_tier: T3
lang: pt
topics: ["entrada", "channels"]
po_id: null
network: aavso
pipeline_stage: help
token_estimate: 542
chunk_hash: "sha256:aa1dbfa7721a105a972bc7154a440f2d67b297d318f8e74e4e2c04e817b4cd23"
corpus_version: 0.1.0-kb1
---

## 3. Metadados comuns (todos os PO-*)

Sempre pedidos (formulário curto ou headers FITS + BD):

| Campo | Obrigatório | Notas |
|-------|-------------|-------|
| `workspace` / site | sim | SiteProfile activo |
| `program_id` (PO-*) | sim | campanha activa |
| `observed_at_utc` | sim | DATE-OBS ou relógio sessão |
| `target` (quando aplicável) | quase sempre | designação + RA/Dec se conhecido |
| `instrument` / config | sim para ciência | telescópio, câmara, filtro |
| `simulated` | sim | flag RN |
| Safety extras | só solar / laser / etc. | checklist |

---

## 4. Mapa por PO-* — como o utilizador fornece a observação

Legenda **Estado**: `feito` / `parcial` / `desenho` (ainda não na UI).

## A — Fotometria / tempo

| PO | Como o utilizador fornece | Canais | Payload mínimo | Produto | Estado |
|----|---------------------------|--------|----------------|---------|--------|
| **A01** Variáveis | Captura lights **ou** importa FITS; indica alvo + estrela comparação (x,y ou catálogo) | IN-CAP, IN-IMP | FITS + band + comp | `light_curve` → AAVSO | parcial (CLI fotometria) |
| **A02** Eruptivas | Igual A01 + cadência / duração da série | IN-CAP, IN-IMP | série densa FITS ou CSV | light_curve | desenho |
| **A03** Cefeidas/RR | Igual A01 + multi-noite (vários plans) | IN-CAP, IN-IMP | várias noites ligadas ao mesmo target | light_curve | desenho |
| **A04** Clusters UBVRI | Importa/captura por filtro; associa filtros UBVRI | IN-CAP, IN-IMP | FITS multi-filtro | tabela cores + FITS | desenho |
| **A05** Trânsitos | Captura série contínua na janela do trânsito; alvo + pred | IN-CAP, IN-IMP, IN-PRED | FITS série / LC | light_curve → ExoClock | parcial |
| **A06** Microlensing | Importa alerta µFUN + série fotométrica densa | IN-PRED, IN-CAP, IN-TAB | alerta + LC | light_curve / CSV | desenho |
| **A07** Rápida | Captura alta cadência (ou CSV de fotómetro) | IN-CAP, IN-TAB | série sub-s | time_series | desenho |
| **A08** Asteroseis | Séries longas (muitas noites) / import CSV | IN-CAP, IN-TAB | time_series longa | time_series | desenho |
| **A09** Asteroides LC | Captura com tracking; alvo MPC | IN-CAP, IN-IMP | FITS + tracking meta | light_curve | desenho |
| **A10** Cometas foto | Igual A09 + filtro/abertura coma | IN-CAP, IN-IMP | FITS + aberturas | fotometria + ICQ | desenho |
