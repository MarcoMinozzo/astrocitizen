---
chunk_id: docs-workflows-006
source_id: docs-workflows
path: docs/WORKFLOWS.md
title: 7.1 Iniciar Sessÿo
trust_tier: T3
lang: pt
topics: ["workflows", "ux"]
po_id: null
network: null
pipeline_stage: help
token_estimate: 369
chunk_hash: "sha256:c17a54fc534da5732f40afddc5a315dfb708ee4eecd54e0155fbcab5f497c4be"
corpus_version: 0.1.0-kb1
---

## 7.1 Iniciar Sessÿo

**Objetivo:** executar blocos do ProgramaDiario com rastreabilidade (RN-056).

| Passo | Aÿÿo | Sistema | Saÿda |
|-------|------|---------|-------|
| 1 | Abrir **Observatÿrio ? Nova sessÿo** | Lista planos `publicado` para Site/data | ÿ |
| 2 | Confirmar ProgramaDiario | **Snapshot** imutÿvel do plano (RN-056) | Sessao + plano congelado |
| 3 | Snapshot meteo inÿcio | RN-022 | CondiÿÿoMeteo ligada ÿ Sessao |
| 4 | Conectar backends (montagem, cÿmera, focuser) | Factory AC-046 | Status conectado / simulado |
| 5 | Estado diÿrio ? `em_execucao` | ÿ | ProgramaDiario atualizado |

**Regra:** comandos slew/exposiÿÿo sÿ com Sessao ativa (RN-090), exceto diagnÿstico.

**Backlog:** AC-050, AC-073.

---

## 7.2 Executar bloco (loop da noite)

| Passo | Aÿÿo | Sistema | Saÿda |
|-------|------|---------|-------|
| 1 | Selecionar prÿximo bloco `agendado` | Opcional: slew via MountPort | Bloco `em_execucao` |
| 2 | Focar / filtro / sequÿncia de exposiÿÿes | CameraPort, FocuserPort | Frames brutos |
| 3 | **Registrar Observaÿÿo** | FITS ? ArtifactStore; metadados ? BD (RN-060ÿ062) | Observacao `bruta` |
| 4 | Marcar bloco `concluido` ou `pulado` (motivo) | ÿ | Status bloco |
| 5 | Repetir atÿ fim da fila ou encerrar | ÿ | ÿ |

**Metadados obrigatÿrios:** Site, UTC, alvo, config. instrumental, bloco/programa, backend cÿmera, meteo, flags (`simulada`, `meteo_manual`).

**Backlog:** AC-051, AC-052, AC-053.

---

## 7.3 Encerrar Sessÿo

| Passo | Aÿÿo | Sistema |
|-------|------|---------|
| 1 | Snapshot meteo fim | RN-022 |
| 2 | Resumo: blocos concluÿdos / pulados / falhou | Log auditÿvel |
| 3 | ProgramaDiario ? `encerrado` | Histÿrico consultÿvel (RN-073) |

---
