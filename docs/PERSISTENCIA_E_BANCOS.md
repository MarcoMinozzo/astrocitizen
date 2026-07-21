# Persistência e bancos de dados

**Decisão:** 2026-07-21  
**Status:** regra de produto e arquitetura (sem implementação nesta fase)  
**Relacionados:** `ESCOPO_GERAL_E_REGRAS_DE_NEGOCIO.md` · `ARQUITETURA.md` (a criar/atualizar) · `STACK_TECNOLOGICA.md`

---

## 1. Princípio

**Todo resultado observacional alimenta bancos de dados.**

Não existe “só arquivo solto” como estado final do fluxo. Arquivos (FITS, CSV, plots) são **artefatos**; a **verdade operacional e científica** da plataforma vive em bases de dados consultáveis, relacionáveis aos programas PO-*, Site, sessão, meteo e equipamento.

Isso vale para:

| Tipo de resultado | Exemplos | Persiste em BD |
|-------------------|----------|----------------|
| Planejamento | ProgramaDiario, blocos, viabilidade céu/meteo | Sim |
| Execução | Sessao, log de instrumentos, falhas | Sim |
| Dados brutos (metadados) | Observacao, path FITS, headers-chave, flags | Sim (arquivo em storage; índice no BD) |
| Calibração | Masters, versões, parâmetros | Sim |
| Análise | ProdutoAnalise (curva de luz, espectro 1D, astrometria, timing…) | Sim |
| Contribuição | ContribuicaoRede (AAVSO, MPC, IOTA, ARAS…) | Sim |
| Contexto | Site, meteo snapshot, configuração instrumental, programa PO-* | Sim |

---

## 2. Modelo lógico (camadas de dados)

```
┌─────────────────────────────────────────────────────────┐
│  Bancos de dados da plataforma (fonte de consulta)      │
│  - operacional / domínio                                │
│  - científico / resultados                              │
│  - (opcional) séries temporais / medições               │
├─────────────────────────────────────────────────────────┤
│  Object storage / filesystem                            │
│  - FITS brutos e reduzidos, plots, exports              │
│  - referenciados por path/URI nas tabelas               │
├─────────────────────────────────────────────────────────┤
│  Caches / externos (não são o arquivo definitivo)       │
│  - efemérides remotas, meteo API (com snapshot no BD)   │
└─────────────────────────────────────────────────────────┘
```

### Separação recomendada (pode ser 1 ou N arquivos/engines)

| Store | Conteúdo | Exemplos de tecnologia (a decidir na implementação) |
|-------|----------|-----------------------------------------------------|
| **Domínio / operacional** | Site, equipamentos, programas, programa diário, sessão, usuários/prefs | SQLite (local) → PostgreSQL (observatório/multi-user) |
| **Resultados científicos** | Observacoes, produtos de análise, medições, versões | Mesmo BD ou schema separado |
| **Séries / pontos** | Pontos de curva de luz, amostras de espectro, timings | Tabelas normalizadas ou particionadas; Parquet opcional depois |
| **Blob / arquivos** | FITS, PNG, PDF de relatório | Disco local ou object store; **sempre** com registro no BD |

Início típico (pequeno observatório): **SQLite + diretório de dados**.  
Evolução: **PostgreSQL** (ou compatível) sem mudar o domínio — via porta `ArchivePort` / `UnitOfWork`.

---

## 3. O que “alimentar o banco” significa na prática

1. Ao **criar/atualizar** ProgramaDiario → commit no BD.  
2. Ao **registrar** Observacao → linha no BD + path do FITS.  
3. Ao **reduzir/analisar** → ProdutoAnalise versionado no BD (+ artefato se houver).  
4. Ao **exportar** para rede → ContribuicaoRede no BD (status do envio).  
5. Snapshots de **meteo** e **efemérides usadas no plano** → BD (rastreabilidade).  

Arquivos órfãos (sem registro) são erro operacional a detectar (job de integridade).

---

## 4. Regras de negócio (persistência)

| ID | Regra |
|----|--------|
| RN-110 | Todo resultado observacional (bruto indexado, calibrado, analisado, exportado) **deve** ter registro em banco de dados. |
| RN-111 | O arquivo FITS/dado bruto é imutável; alterações de redução geram **nova versão** de produto no BD, não overwrite silencioso. |
| RN-112 | Consultas de gestão (por programa PO-*, site, data, alvo, rede) são feitas **via BD**, não varrendo pastas como fonte primária. |
| RN-113 | Efemérides/meteo obtidos de API e usados numa decisão de plano ou observação são **persistidos (snapshot)** no BD. |
| RN-114 | Soft-delete / arquivamento lógico no BD; purge físico de arquivos só com política explícita e trilha de auditoria. |
| RN-115 | Dados simulados (`simulada=true`) também vão ao BD, sempre filtráveis e excluíveis de exports oficiais. |
| RN-116 | Schema versionado (migrações); upgrades da plataforma não quebram histórico. |

---

## 5. Implicação arquitetural

Na arquitetura hexagonal / monólito modular:

- O domínio emite intenções (“ObservacaoRegistrada”, “ProdutoAnaliseCriado”).  
- Um **adapter de persistência** (`SqlArchiveAdapter`, etc.) grava no BD.  
- UI/CLI **nunca** “salvam só em pasta” sem passar pelo caso de uso que persiste.  
- Análise e programas PO-* **leem** resultados do BD para curvas, relatórios e programa diário futuro.

Isso habilita: histórico, multi-programa, estatísticas do observatório, reprocessamento e contribuição a redes com rastreio.

---

## 6. Identificadores e rastreabilidade

Todo registro relevante carrega, quando aplicável:

- `site_id`, `program_id` (PO-*), `daily_plan_id`, `session_id`, `observation_id`  
- tempo (UTC), alvo, configuração instrumental  
- `artifact_uri` (FITS/plot)  
- `content_hash` (opcional, integridade)  
- `schema_version` / `pipeline_version`  

---

## 7. Privacidade e backup

- Credenciais de redes **não** ficam em claro no BD de resultados.  
- Backup = BD + árvore de artefatos referenciados.  
- Export completo do observatório = dump BD + pacote de arquivos.

---

## 8. Fora de escopo (por enquanto)

- Escolher engine definitiva (SQLite vs PostgreSQL) — decisão de implementação.  
- Data lake / warehouse na nuvem — evolução possível, não requisito do MVP.  
- BD científico externo (ex.: só AAVSO) — a plataforma **alimenta o BD próprio** e **exporta**; o BD da rede é destino, não substituto do arquivo local.
