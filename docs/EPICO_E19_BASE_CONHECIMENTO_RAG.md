# Epico E19 — Base de conhecimento interna para RAG

**Prioridade:** P2–P3  
**Estado:** aberto (backlog)  
**Dependencias:** E1 (persistencia), corpus documental existente (`docs/`, atlas, literatura indexada)  
**Consumidores previstos:** assistente de ajuda, narrativa LLM sobre produtos (ex.: AC-107 spectrum), labs (E18)

---

## 1. Objetivo

Criar uma **base de dados / indice interno de conhecimento** que sirva de fundamento a um pipeline **RAG** (Retrieval-Augmented Generation):

1. Ingerir fontes confiaveis do projeto (docs oficiais, atlas de redes, guias PO-*, resumos de literatura).
2. Fragmentar, metadatar e (opcionalmente) embeddar.
3. Recuperar trechos relevantes perante uma pergunta ou um produto de analise.
4. So entao (opcional) gerar texto com LLM **ancorado** nesses trechos.

Sem esta base, um LLM tenderia a alucinar procedimentos de redes (AAVSO, BeSS, MPC, …).

---

## 2. Principios

| Principio | Detalhe |
|-----------|---------|
| Fontes versionadas | Cada chunk aponta para path + hash / versao do doc |
| Licencas | So corpus com direitos claros; literatura externa = resumo/citacao, nao PDF pirata |
| Local-first | Indice utilizavel offline no Desktop quando possivel (D-010 / DoD) |
| Medidas != prosa | RAG/LLM **nao** substituem fotometria, spectrum-report, plate-solve |
| Opt-in | Assistente desligavel; fluxos cientificos continuam sem rede/LLM |
| Citacoes | Toda resposta RAG deve listar `source_id` / trecho |

---

## 3. Escopo da base (v1)

### Incluir

- `docs/` de produto (workflows, programas, atlas, entrada de dados, sprints estaveis)
- Atlas de reporte (`docs/atlas/`)
- Indice de literatura (`LITERATURA_INDICE.md`) e fichas curtas geradas pelo projeto
- Guias por PO-* (receitas minimas)
- Relatorios estruturados da propria plataforma (opcional: `spectrum_report`, checklists) como **contexto de sessao**, nao como corpus global

### Excluir (v1)

- FITS brutos / pixel data
- Credenciais
- Dados pessoais de observadores sem consentimento
- Scraping indiscriminado da web

---

## 4. Arquitetura alvo (alto nivel)

```text
Corpus (markdown/JSON)
        |
        v
  Ingestor (chunk + metadata + license)
        |
        v
  KnowledgeStore (SQLite/PG + ficheiros)
        +-- documents / chunks
        +-- embeddings (vector local ou extensao)
        |
        v
  RetrieverPort.retrieve(query, filters) -> Passage[]
        |
        +--> UI Ajuda / CLI ask
        +--> LLM narrator (AC-107) com passages + spectrum_report
```

Adapters: comecar com **SQLite + FTS5** (ou similar) e evoluir para embeddings locais; vector DB remoto so se necessario (ver MODELO_DADOS — E19 promove o que estava “adiado”).

---

## 5. Itens de backlog

Ver secao **E19** em [PRODUCT_BACKLOG.md](PRODUCT_BACKLOG.md) (AC-190…AC-196).

Ordem sugerida:

1. Modelo de documentos/chunks + ingestao do `docs/`  
2. Retriever lexical (FTS) + CLI smoke  
3. Embeddings locais + hibrido lexical/vector  
4. Ligacao a AC-107 (narrativa espectral grounded)  
5. Painel Ajuda na GUI  

---

## 6. Criterios de aceite do epico (DoD)

- [ ] Corpus interno versionado e auditavel  
- [ ] Retriever devolve passagens com citacao  
- [ ] Funciona sem LLM (so retrieval)  
- [ ] LLM (se ativo) recusa inventar factos fora das passagens + produtos  
- [ ] Docs de arquitectura + testes de ingestao/retriever  
- [ ] Alinhado a D-010 (tamanho de indice, custo de embed, opt-in)
