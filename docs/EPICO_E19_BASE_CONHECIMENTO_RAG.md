# Epico E19 — Base de conhecimento interna para RAG

**Prioridade:** P2–P3  
**Estado:** aberto (backlog) · **KB-0 scaffold ✅** (AC-190, 2026-07-23) · alinhado ao processo Vectron KB/MCP (2026-07)  
**Dependencias:** E1 (persistencia), corpus documental existente (`docs/`, atlas, literatura indexada)  
**Consumidores previstos:** assistente de ajuda, narrativa LLM sobre produtos (ex.: AC-107 spectrum), labs (E18), futuro modulo SaaS  
**Referencia cruzada:** motorsport-agent — *Pre-projeto Knowledge Base MCP Coaching (2026-07)* e *Sprint BL-KB*

---

## 1. Objetivo

Criar uma **base de dados / indice interno de conhecimento** que sirva de fundamento a um pipeline **RAG** (Retrieval-Augmented Generation), com exposicao tipica via **RetrieverPort** e, quando fizer sentido, **tools MCP** (Model Context Protocol) so de leitura:

1. Catalogar fontes (catalogo + licencas + trust tiers).
2. Ingerir offline (nunca PDF na pergunta).
3. Fragmentar com metadados e (opcionalmente) embeddar.
4. Recuperar trechos relevantes perante pergunta ou produto de analise.
5. So entao (opcional) gerar texto com LLM **ancorado** nesses trechos + citacoes.

Sem esta base, um LLM tenderia a alucinar procedimentos de redes (AAVSO, BeSS, MPC asteroides, …).

---

## 2. Principios

| Principio | Detalhe |
|-----------|---------|
| Fontes versionadas | Cada chunk aponta para path + hash / versao do doc |
| Licencas | So corpus com direitos claros; literatura externa = resumo/citacao, nao PDF pirata |
| Local-first | Indice utilizavel offline no Desktop (SQLite FTS5); SaaS pode reusar PG + FTS/pgvector |
| Medidas != prosa | RAG/LLM **nao** substituem fotometria, spectrum-report, plate-solve |
| Opt-in | Assistente desligavel; fluxos cientificos continuam sem rede/LLM |
| Citacoes | Toda resposta RAG deve listar `chunk_id` / `source_id` / `trust_tier` |
| Custo infra | Preferir FTS + embeddings locais; evitar vector DB SaaS no MVP (como BL-KB €0) |
| KB != sessao | Corpus estatico separado de dados do observador (FITS, produtos); estes entram como **contexto de sessao** |

---

## 3. Comparativo com motorsport (KB + MCP)

O estudo Vectron (*Knowledge Base MCP Coaching*) ja fechou **KB-0** (scaffold + politica) e avanca conteudo/ingest. AstroCitizen E19 esta no equivalente a **abrir o epico** (docs + backlog). Muito do **processo** e reutilizavel; a **runtime** adapta-se ao Desktop.

| Tema | Motorsport (Vectron) | AstroCitizen (E19) | Complementar? |
|------|----------------------|--------------------|---------------|
| Camadas A→E | Catalogo → processed → chunks → indice → MCP | Idem em espirito; MCP opcional apos RetrieverPort | **Sim** — adoptar fases KB-0…5 |
| Trust tiers T1–T5 | Papers / livros / docs plataforma / pratico / abstract | Idem: literatura astro / atlas redes / docs AstroCitizen | **Sim** — politica de conflito |
| Conflito | T3 (plataforma) > T1 em “como o produto funciona”; T1 > T3 em ciencia | Igual: docs PO/RN > paper se conflito de UX; paper > docs em fisica | **Sim** |
| FTS primeiro | Postgres `tsvector` Fase 0 | SQLite **FTS5** Desktop; PG no SaaS | **Sim** — mesma ordem |
| Embeddings | pgvector + `multilingual-e5-small` local | Extensao local / ficheiro; depois PG no cloud | **Sim** — hibrido RRF depois |
| MCP tools | `kb_search`, `kb_get_chunk`, `kb_get_glossary` | Mesmas tools + filtros `po_id` / `network` | **Sim** — AC-197 |
| Glossario | Sync `telemetry-glossary.ts` ↔ chunks | Glossario espectral / redes / PO termos | **Sim** — AC-198 |
| QA | Gold set 30 perguntas; citation rate ≥80% | Gold set astronomia+plataforma | **Sim** — AC-199 |
| Sessao vs KB | Telemetria via tools separadas | `spectrum_report` / produtos via tools/contexto, nao no corpus | **Ja alinhado** |
| Ingestao | Offline PyMuPDF/Docling; PDF gitignored | Offline; literature workspaces → notas/chunks | **Sim** |
| Scaffold pastas | `knowledge-base/` (catalog, taxonomy, licenses, qa) | Criar espelho em `knowledge-base/` ou `docs/kb/` | **Sim** — AC-190b |
| Runtime | SaaS API + Claude | Desktop-first; SaaS depois (D-008) | Adaptar, nao copiar cego |
| Hot path | Heuristicas H* imutaveis; LLM depois | AC-106 deterministico imutavel; LLM AC-107 depois | **Ja alinhado** |

### O que AstroCitizen ja cobre bem

- Separacao medidas / prosa (AC-106 vs AC-107).
- Opt-in e citacoes no DoD do epico.
- Consumidor piloto claro: narrativa espectral + ajuda PO-*.

### Lacunas do E19 que o processo motorsport preenche

1. **Scaffold KB-0** antes de codigo (catalog.json, taxonomy, manifest, licenses, chunk template).
2. **Trust tiers + politica de conflito** explicitas.
3. **Taxonomia** (`topics`, `pipeline_stages` / modos Analisar, `po_id`, `network`).
4. **MCP contract** (tools read-only) alem do RetrieverPort interno.
5. **Gold questions + citation rate** como DoD mensuravel.
6. **Glossario** alinhado UI/CLI.
7. **Fases numeradas** com gate de PO (nao misturar INT LLM com ingest incompleto).

---

## 4. Escopo da base (v1)

### Incluir

- `docs/` de produto (workflows, programas, atlas, entrada de dados, sprints estaveis) — **trust T3**
- Atlas de reporte (`docs/atlas/`) — T3 / T4 conforme fonte oficial da rede
- Indice de literatura + fichas curtas do projeto — T1/T2/T5 conforme origem
- Guias por PO-* (receitas minimas) — T3
- Relatorios estruturados da plataforma (`spectrum_report`, checklists) como **contexto de sessao**, nao corpus global

### Excluir (v1)

- FITS brutos / pixel data
- Credenciais
- Dados pessoais de observadores sem consentimento
- Scraping indiscriminado da web
- PDF de livros completos no git

---

## 5. Arquitetura alvo

```text
A  catalog.json + taxonomy + licenses + bibliografia
B  processed/*.md (ingest offline)
C  chunks/v1 (300-800 tokens, frontmatter, chunk_hash)
D  indice: SQLite FTS5 (Desktop) / PG FTS (SaaS) → embeddings locais → RRF
E  RetrieverPort + (opcional) MCP: kb_search / kb_get_chunk / kb_get_glossary
        |
        +--> CLI knowledge search / UI Ajuda
        +--> LLM narrator (AC-107) + spectrum_report (sessao)
```

**Dois canais (como no Vectron):**

| Canal | Exemplo | Tool / API |
|-------|---------|------------|
| KB estatica | “O que e a banda O2 A?” | `kb_search` |
| Sessao observador | “Explica *este* spectrum_report” | produto + passagens KB |

---

## 6. Fases de entrega (espelho BL-KB)

| Fase | Nome | DoD resumido |
|------|------|--------------|
| **KB-0** | Docs + scaffold | ✅ `knowledge-base/` + taxonomy (AC-190) |
| **KB-1** | Conteudo inicial | ✅ ≥50 chunks T3 (AC-192) |
| **KB-2** | Ingest + FTS | ✅ FTS5 + `knowledge search` (AC-193); gold-questions v0 placeholder |
| **KB-3** | Retriever + MCP read-only | ✅ RetrieverPort (AC-194); MCP AC-197; citation rate AC-199 |
| **KB-4** | Hibrido vector | Embeddings locais + RRF |
| **KB-5** | Produto | AC-107 + Ajuda GUI; sem regressao AC-106 |

---

## 7. Itens de backlog

Ver secao **E19** em [PRODUCT_BACKLOG.md](PRODUCT_BACKLOG.md) (AC-190…AC-200).

Ordem sugerida:

1. Scaffold + taxonomy + catalog (KB-0)  
2. Ingestao T3 `docs/` + atlas  
3. FTS + CLI search  
4. Gold QA + citation eval  
5. MCP tools (ou adapter)  
6. Embeddings hibridos  
7. AC-107 + Ajuda GUI  

---

## 8. Criterios de aceite do epico (DoD)

- [ ] Corpus interno versionado e auditavel (catalog + licenses)  
- [ ] Trust tiers e politica de conflito documentados  
- [ ] Retriever devolve passagens com `chunk_id` / citacao  
- [ ] Funciona sem LLM (so retrieval)  
- [ ] Gold set + citation rate alvo definido (ex. ≥80% factuais)  
- [ ] LLM (se ativo) recusa inventar factos fora das passagens + produtos  
- [ ] AC-106 / pipelines cientificos sem regressao  
- [ ] Alinhado a D-010 (tamanho de indice, custo de embed, opt-in)
