---
chunk_id: docs-workflows-010
source_id: docs-workflows
path: docs/WORKFLOWS.md
title: 11. Variaÿÿes por famÿlia PO-* (resumo)
trust_tier: T3
lang: pt
topics: ["workflows", "ux"]
po_id: PO-A01
network: mpc
pipeline_stage: help
token_estimate: 418
chunk_hash: "sha256:dde79f14356e30cc72a30a9fda41763f4112f4a0f3ba0845db071ad81356fb72"
corpus_version: 0.1.0-kb1
---

## 11. Variaÿÿes por famÿlia PO-* (resumo)

| Famÿlia | Diferenÿa na jornada (vs. PO-A01) |
|---------|-----------------------------------|
| **PO-B** (espectro) | Blocos com config. espectrÿgrafo; anÿlise = extraÿÿo 1D + ?; export ARAS/BeSS |
| **PO-C** (NEO/SN) | Efemÿrides Horizons/MPC; astrometria/blink; export MPC/TNS |
| **PO-D** (IOTA) | Janelas estreitas + margem (RN-013); timing de alta precisÿo; export IOTA |
| **PO-E** (solar/planetÿrio) | Regras de cÿu diurno (exceÿÿo RN-012); filtros solares obrigatÿrios |
| **PO-J** (calibraÿÿo/meteo) | Blocos de flat/dark/bias; produto = masters + perfil meteo site |

Cada template PO-* reutiliza os **mesmos quatro modos**; plugins alteram validaÿÿo, anÿlise e export (ARQUITETURA ÿ5).

---

## 12. Matriz modo ÿ artefato de domÿnio

| Artefato | Configurar | Planejar | Executar | Analisar | Contribuir |
|----------|:----------:|:--------:|:--------:|:--------:|:----------:|
| Site | C/R/U | R | R | R | R |
| Equipamento | C/R/U | R | R | ÿ | ÿ |
| ProgramaObservacional | C/R/U | R | R | R | R |
| ProgramaDiario | ÿ | C/R/U | R | R | ÿ |
| Sessao | ÿ | ÿ | C/U | R | ÿ |
| Observacao | ÿ | ÿ | C | R/U | R |
| ProdutoAnalise | ÿ | ÿ | ÿ | C/R/U | R |
| ContribuicaoRede | ÿ | ÿ | ÿ | R | C/R/U |

Legenda: C criar, R ler, U atualizar.

---

## 13. Mapeamento casos de uso ? backlog

| Caso de uso | Itens AC-* principais |
|-------------|------------------------|
| `GerirSite` | AC-020, AC-072 |
| `GerirEquipamento` | AC-021, AC-040ÿ047, AC-072 |
| `GerirProgramas` | AC-022, AC-023, AC-074, AC-081ÿ088 |
| `PlanejarDia` | AC-030ÿ037, AC-073 |
| `ExecutarSessao` | AC-050, AC-053, AC-073 |
| `RegistrarObservacao` | AC-051, AC-052, AC-054 |
| `Analisar` | AC-060ÿ063, AC-090ÿ105, AC-110ÿ |
| `ExportarRede` | E14, atlas, AC-093+ |

---
