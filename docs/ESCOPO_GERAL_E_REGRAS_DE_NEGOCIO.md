# Escopo geral e regras de negócio

**Produto:** Plataforma de Astronomia Observacional Cidadã  
**Status:** Fase 0 — especificação de negócio (sem implementação)  
**Data:** 2026-07-20  
**Documentos relacionados:**  
`PLATAFORMA_OBSERVACIONAL.md` · `ESCOPO_CITIZEN_SCIENCE.md` · `STACK_TECNOLOGICA.md` · `REVISAO_ASTRONOMIA_OBSERVACIONAL.md`

---

## 1. Propósito do produto

A plataforma existe para **obter, planejar, executar, registrar e analisar observações astronômicas** no contexto de citizen science e pequenos observatórios.

Ela concentra cinco eixos de negócio inseparáveis:

1. **Dados astronômicos e efemérides observacionais** — o que está no céu, quando e onde observar.  
2. **Meteorologia do local de observação** — se as condições permitem observar.  
3. **Programa observacional diário** — o plano concreto da noite/dia.  
4. **Planejamento de observações e de equipamento** — alvos + instrumentos adequados.  
5. **Registro, análise e gestão dos programas observacionais** — do dado bruto ao produto científico e à campanha contínua.
6. **Persistência em bancos de dados** — todo resultado observacional alimenta BD(s) consultáveis (ver `PERSISTENCIA_E_BANCOS.md`).

O catálogo oficial de programas está em `PROGRAMAS_OBSERVACIONAIS.md` (PO-*, classes A–K). `ESCOPO_CITIZEN_SCIENCE.md` detalha capacidades científicas transversais. Este documento define **como o negócio opera** (programa diário, meteo, equipamento, registro, gestão).

---

## 2. Escopo geral (capacidade de negócio)

### 2.1 Em escopo

| Capacidade | Descrição |
|------------|-----------|
| **Catálogo / resolução de alvos** | Identificar objetos (nome, coordenadas, tipo) via serviços e catálogos. |
| **Efemérides observacionais** | Posição, altitude/azimute, nascer/ocaso, janelas de visibilidade, eventos (trânsito, ocultação, oposição, etc.) para o **site** e o **intervalo de tempo** escolhidos. |
| **Meteorologia do site** | Condições atuais e previsão no local de observação (nuvens, vento, umidade, precipitação, temperatura, seeing estimado quando disponível). |
| **Perfis de site** | Locais de observação com coordenadas, altitude, fuso, horizonte/obstáculos opcionais. |
| **Inventário de equipamento** | Montagens, câmeras, focuser, filtros, espectrógrafos, etc., com estado e compatibilidade. |
| **Planejamento de equipamento** | Escolher/validar o conjunto instrumental para cada observação ou programa do dia. |
| **Programas observacionais** | Campanhas científicas cidadãs (variáveis, NEO, ARAS, IOTA, solar, …) com regras, alvos e entregáveis. |
| **Programa diário** | Agenda do dia/noite: sequência de blocos observacionais derivados dos programas ativos + efemérides + meteo + equipamento. |
| **Execução / aquisição** | Controle de instrumentos (Alpaca/udrv) conforme o plano, quando o usuário iniciar a sessão. |
| **Registro de observações** | Metadados, FITS/dados brutos, log de sessão, condições meteo no momento, equipamento usado. |
| **Análise** | Redução e medidas conforme o tipo de programa (fotometria, espectro, astrometria, timing, …). |
| **Gestão de programas** | Criar, ativar, pausar, priorizar, arquivar programas; acompanhar progresso e contribuições a redes. |
| **Exportação / reporte** | Formatos exigidos pelas redes cidadãs (AAVSO, MPC, IOTA, ARAS/BeSS, etc.). |

### 2.2 Fora de escopo (negócio)

- Ensino teórico de astrofísica como produto principal.  
- Projeto civil / CAD de observatório.  
- Previsão meteorológica global genérica sem vínculo ao site de observação.  
- Substituição obrigatória de todos os softwares especializados externos (a plataforma **orquestra e integra**; pode importar previsões IOTA, etc.).  
- Redistribuição de drivers proprietários.

---

## 3. Atores

| Ator | Papel |
|------|-------|
| **Observador** | Planeja, executa, registra e analisa observações. |
| **Gestor de programa** | (Pode ser o mesmo usuário) define campanhas, prioridades e critérios de sucesso. |
| **Sistema** | Calcula efemérides, consulta meteo/serviços, valida regras, agenda o programa diário. |
| **Instrumento** | Montagem, câmera, focuser, etc., via backends de hardware. |
| **Rede cidadã** | Destino externo de dados (AAVSO, MPC, …) — consumidor dos exports. |

Na versão inicial (usuário único / pequeno observatório), Observador e Gestor de programa são o mesmo perfil. Multi-usuário fica como evolução.

---

## 4. Entidades de domínio (modelo de negócio)

| Entidade | Descrição |
|----------|-----------|
| **Site** | Local de observação (`SiteProfile`: nome, lat, lon, alt, fuso, horizonte). |
| **CondiçãoMeteo** | Snapshot ou previsão associada a Site + instante/intervalo. |
| **Alvo** | Objeto celeste ou região (coordenadas, tipo, identificadores externos). |
| **Efeméride** | Quantidades observacionais do Alvo no Site em um tempo (Alt/Az, HA, airmass, eventos). |
| **Equipamento** | Item físico ou lógico (montagem, câmera, focuser, filtro, espectrógrafo…). |
| **ConfiguraçãoInstrumental** | Conjunto de Equipamentos usados juntos numa observação. |
| **ProgramaObservacional** | Campanha de longo prazo (tipo científico, regras, alvos, cadência, rede de destino). |
| **BlocoObservacional** | Unidade planejada: Alvo + técnica + exposição(ões) + equipamento + janela temporal. |
| **ProgramaDiario** | Conjunto ordenado de Blocos para uma data (e Site), com status. |
| **Sessao** | Execução real de (parte do) ProgramaDiario. |
| **Observacao** | Registro de uma aquisição/medida (dados + metadados + meteo + equipamento). |
| **ProdutoAnalise** | Resultado derivado (curva de luz, espectro 1D, astrometria, relatório de ocultação…). |
| **ContribuicaoRede** | Pacote exportado / enviado / a enviar para uma rede cidadã. |

---

## 5. Fluxo de negócio principal (dia a dia)

```
[Site] + [Programas ativos]
        ↓
[Efemérides] + [Meteo do site] + [Inventário de equipamento]
        ↓
   Planejar Programa Diário
        ↓
   Validar viabilidade (céu + meteo + equipamento)
        ↓
   Executar Sessão (opcional / quando houver hardware)
        ↓
   Registrar Observações
        ↓
   Analisar → Produtos
        ↓
   Atualizar Programas + Exportar para redes
```

O sistema deve permitir usar só o trecho de **planejamento** (sem hardware) e só o trecho de **análise** (dados já adquiridos).

---

## 6. Regras de negócio

Convenção: **RN-XXX** — obrigatórias salvo indicação “desejável”.

### 6.1 Site e tempo

| ID | Regra |
|----|--------|
| RN-001 | Toda efeméride, meteo e programa diário são relativos a um **Site** explícito. Não existe “céu genérico” sem local. |
| RN-002 | O Site ativo pode ser alterado; ao mudar o Site, efemérides e viabilidade do ProgramaDiario devem ser **recalculadas**. |
| RN-003 | Tempos de observação, headers e logs usam escala de tempo explícita (UTC obrigatório nos dados; hora local apenas na UI). |
| RN-004 | Datas do ProgramaDiario referem-se à **noite civil** do Site (configurável: crepúsculo astronômico / horário local de início). |

### 6.2 Efemérides e dados astronômicos

| ID | Regra |
|----|--------|
| RN-010 | Efemérides observacionais (Alt/Az, airmass, nascer/ocaso, trânsito meridiano) são calculadas com **Astropy** a partir de coordenadas/tempo/site. |
| RN-011 | Efemérides de corpos do Sistema Solar / NEOs usam serviços confiáveis (**Astroquery**/Horizons/MPC) quando a precisão orbital for necessária. |
| RN-012 | Um BlocoObservacional só pode ser marcado **viável no céu** se, na janela planejada, altitude ≥ limite do Programa (default configurável, ex.: 25°) e fora do Sol (exceto programas solares). |
| RN-013 | Eventos temporais críticos (ocultações, trânsitos) têm janela com margem de segurança definida pelo ProgramaObservacional. |
| RN-014 | Falha de rede ao obter efemérides remotas não apaga o plano: o sistema usa cache local ou marca o bloco como **efeméride indisponível**. |

### 6.3 Meteorologia do local

| ID | Regra |
|----|--------|
| RN-020 | O ProgramaDiario consulta **meteorologia do Site** (atual e/ou previsão para a janela da noite). |
| RN-021 | Condições mínimas (cobertura de nuvens, vento, precipitação, umidade) são limiares do Site ou do Programa; abaixo/acima do limiar o bloco fica **inviável por meteo** (não é excluído do histórico — fica justificado). |
| RN-022 | No início e no fim da Sessao, o sistema registra um snapshot de CondiçãoMeteo ligado às Observacoes. |
| RN-023 | Se a fonte meteo estiver indisponível, o usuário pode **sobrescrever manualmente** a decisão de observar (com flag `meteo_manual=true` no registro). |
| RN-024 | Meteo é sempre do **local de observação**, não de uma cidade arbitrária sem vínculo ao Site. |

### 6.4 Equipamento e planejamento instrumental

| ID | Regra |
|----|--------|
| RN-030 | Todo BlocoObservacional declara uma **ConfiguraçãoInstrumental** (ou herda a padrão do Programa). |
| RN-031 | O planejamento de equipamento valida: equipamento **disponível**, **compatível** com a técnica (ex.: espectrógrafo para espectroscopia) e **conectado/selecionável** no backend quando a sessão for instrumental. |
| RN-032 | Câmera: o usuário escolhe backend **udrv** ou **alpaca** (ou simulador); a escolha fica registrada na Observacao. |
| RN-033 | Montagem e focuser, quando exigidos pelo bloco, devem estar definidos na configuração; ausência gera status **equipamento incompleto**. |
| RN-034 | Mudança de equipamento no meio da Sessao gera novo trecho de log e metadados (não sobrescrever o anterior). |
| RN-035 | Inventário de equipamento é por observatório/usuário; itens podem ser marcados indisponíveis (manutenção). |

### 6.5 Programas observacionais

| ID | Regra |
|----|--------|
| RN-040 | Um ProgramaObservacional tem: tipo (domínio CS-*), objetivos, cadência, critérios de alvo, técnica, rede(s) de destino, prioridade, estado (`ativo` \| `pausado` \| `arquivado`). |
| RN-041 | Só programas **ativos** geram candidatos automaticamente no ProgramaDiario. |
| RN-042 | O sistema gerencia **múltiplos programas em paralelo**; conflitos de horário são resolvidos por **prioridade** e depois por janela de altitude/evento. |
| RN-043 | Cada programa define o **produto mínimo aceitável** (ex.: curva de luz diferencial; espectro λ-calibrado; astrometria MPC). |
| RN-044 | Programas ligados a redes (AAVSO, MPC, IOTA, ARAS…) devem conhecer o **formato de exportação** exigido. |
| RN-045 | Pausar um programa não apaga histórico nem Observacoes já feitas. |
| RN-046 | Todo ProgramaObservacional ativo deriva de um template **PO-*** do catálogo oficial (`PROGRAMAS_OBSERVACIONAIS.md`), ou é extensão documentada dele. |
| RN-047 | Novos tipos de programa fora do catálogo PO-* só entram após atualização formal desse catálogo. |

### 6.6 Programa diário e planejamento de observações

| ID | Regra |
|----|--------|
| RN-050 | Existe no máximo **um ProgramaDiario vigente por Site e por data de noite**. |
| RN-051 | O ProgramaDiario é gerado/atualizado a partir de: programas ativos + efemérides + meteo + equipamento disponível. |
| RN-052 | O observador pode **editar** o programa diário (reordenar, incluir alvo manual, remover bloco) sem alterar a definição do ProgramaObservacional. |
| RN-053 | Cada bloco no diário tem status: `candidato` \| `agendado` \| `inviavel_ceu` \| `inviavel_meteo` \| `inviavel_equip` \| `em_execucao` \| `concluido` \| `pulado` \| `falhou`. |
| RN-054 | Blocos inviáveis permanecem visíveis com **motivo** (transparência do planejamento). |
| RN-055 | O planejamento pode ser feito **sem hardware** (modo planejamento puro). |
| RN-056 | Ao iniciar a Sessao, o sistema trava a versão do ProgramaDiario usada (snapshot) para rastreabilidade. |

### 6.7 Registro de observações

| ID | Regra |
|----|--------|
| RN-060 | Toda Observacao referencia: Site, tempo, Alvo (se houver), ConfiguraçãoInstrumental, Bloco/Programa (se houver), CondiçãoMeteo (se disponível). |
| RN-061 | Dados brutos (FITS etc.) não são alterados após a gravação; reduções geram **ProdutosAnalise** versionados. |
| RN-062 | Headers/metadados devem permitir reconstruir as condições da noite (site, equipamento, meteo, programa). |
| RN-063 | Observacoes podem existir **fora** de um ProgramaDiario (aquisição ad hoc), mas devem poder ser **associadas depois** a um programa. |
| RN-064 | Exclusão de Observacao é lógica (arquivamento); não apagar arquivos sem confirmação explícita. |

### 6.8 Análise

| ID | Regra |
|----|--------|
| RN-070 | A análise disponível depende do **tipo do ProgramaObservacional** / técnica do bloco (fotometria, espectro, astrometria, timing, imaging…). |
| RN-071 | Todo ProdutoAnalise referencia as Observacoes de origem e os parâmetros de redução. |
| RN-072 | Reprocessar gera nova versão do produto; a versão “publicável” é marcada explicitamente pelo observador. |
| RN-073 | Análise pode ocorrer dias após a aquisição; o ProgramaDiario histórico permanece consultável. |

### 6.9 Contribuição e redes

| ID | Regra |
|----|--------|
| RN-080 | Exportação para rede só é permitida se o ProdutoAnalise atender o **produto mínimo** do programa (RN-043). |
| RN-081 | Cada ContribuicaoRede registra status `rascunho` \| `validado` \| `exportado` \| `enviado` \| `rejeitado`. |
| RN-082 | Credenciais de redes não ficam em texto claro no repositório de dados do projeto; uso de segredo local do usuário. |

### 6.10 Hardware e execução

| ID | Regra |
|----|--------|
| RN-090 | Comandos de slew/exposição só ocorrem com confirmação de Sessao ativa (exceto modo diagnóstico). |
| RN-091 | Simulador é equivalente funcional para planejamento/treino/CI; Observacoes simuladas são flagadas `simulada=true`. |
| RN-092 | Falha de instrumento marca o bloco como `falhou` e **não** avança automaticamente para o próximo sem política do programa (default: pausar e alertar). |

### 6.11 Integridade e auditoria

| ID | Regra |
|----|--------|
| RN-100 | Ações que alteram ProgramaDiario, Programas, Inventário ou exclusões geram entrada de log auditável. |
| RN-101 | Preferências e limiares (altitude mínima, meteo) são por Site e/ou Programa, com defaults da plataforma. |

---


### 6.12 Persistência e bancos de dados

| ID | Regra |
|----|--------|
| RN-110 | Todo resultado observacional alimenta **banco(s) de dados**; arquivo sozinho não é estado final. |
| RN-111 | FITS/bruto imutável; reduções = novas versões de produto no BD. |
| RN-112 | Consultas de gestão e ciência usam o BD como fonte primária (artefatos são referenciados). |
| RN-113 | Snapshots de meteo/efemérides usados em decisões são persistidos. |
| RN-114 | Exclusão lógica + auditoria; purge físico só com política explícita. |
| RN-115 | Observações simuladas também entram no BD, marcadas e filtráveis. |
| RN-116 | Schema versionado com migrações. |

Detalhe: `PERSISTENCIA_E_BANCOS.md`.

## 7. Estados resumidos

### ProgramaObservacional
`rascunho` → `ativo` ⇄ `pausado` → `arquivado`

### ProgramaDiario
`rascunho` → `publicado` → `em_execucao` → `encerrado`

### BlocoObservacional
ver RN-053

### Observacao
`bruta` → `calibrada` → `analisada` → `publicavel` / `arquivada`

---

## 8. Requisitos de informação mínimos

### Programa diário (saída do planejamento)

Para cada bloco: alvo, janela UT, altitude prevista, airmass, status céu/meteo/equip, configuração instrumental, programa de origem, prioridade, notas.

### Registro de observação

Identificadores, tempos, site, meteo, equipamento/backend, arquivos de dados, vínculo a bloco/programa, flags (simulada, meteo_manual).

### Painel de gestão de programas

Lista de programas, estado, próxima janela útil, observações recentes, contribuições pendentes, alertas (meteo ruim, efeméride falhou, equipamento indisponível).

---

## 9. Fontes de dados (negócio → tecnologia)

| Necessidade de negócio | Fonte típica |
|------------------------|--------------|
| Coordenadas / tempo / AltAz | Astropy |
| NEOs / órbitas / Horizons | Astroquery |
| Nomes de alvos | SIMBAD / catálogos |
| Meteo do site | API meteo +/ou ASCOM ObservingConditions + entrada manual |
| Controle instrumental | Alpyca / udrv SBIG / simulador |
| Previsões de ocultação | Import IOTA / arquivos de previsão |

Detalhe técnico: `STACK_TECNOLOGICA.md`.

---

## 10. Critérios de aceite de negócio (Fase de produto)

A especificação de negócio está atendida quando o sistema permitir, de ponta a ponta:

1. Cadastrar Site e equipamento.  
2. Ativar pelo menos dois ProgramasObservacionais distintos.  
3. Gerar ProgramaDiario com efemérides + meteo + validação de equipamento.  
4. Executar ou importar Observacoes e analisá-las conforme o tipo.  
5. Atualizar o estado dos programas e preparar export para rede.  

A cobertura de **todos** os tipos científicos permanece em `ESCOPO_CITIZEN_SCIENCE.md`; este documento garante o **esqueleto operacional** comum a todos eles.

---

## 11. Próximos artefatos derivados

| Artefato | Conteúdo |
|----------|----------|
| `WORKFLOWS.md` | Fluxos UI passo a passo (planejar noite, executar, analisar) |
| `API_ALVO.md` | Contratos dos serviços de domínio (Site, Ephemeris, Meteo, Program, DailyPlan…) |
| Atualização `BACKLOG.md` | Épicos BN-* mapeados às RN |

---

## 12. Glossário rápido

| Termo | Significado |
|-------|-------------|
| Efeméride observacional | Posição/circunstância do alvo **como vista do Site** no tempo T |
| Programa observacional | Campanha científica contínua |
| Programa diário | Plano da noite/dia para um Site |
| Configuração instrumental | Conjunto de equipamentos da observação |
| Citizen science | Produção de dados astronômicos úteis a redes/ciência por não-profissionais ou pequenos observatórios |
