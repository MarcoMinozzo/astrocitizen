# Arquitetura — AstroCitizen

**Decisão:** monólito modular + arquitetura hexagonal (Ports & Adapters) + DDD + plugins PO-*  
**Deploy:** dois módulos de produto — **SaaS** + **Desktop** (ver D-008)  
**Data:** 2026-07-21  
**Status:** especificação

> **Arquitetura de produto (SaaS + Desktop):** [ARQUITETURA_SAAS_DESKTOP.md](ARQUITETURA_SAAS_DESKTOP.md)  
> Este documento descreve a forma **interna** do software (hexagonal, bounded contexts, ports).

---

## 1. Forma do sistema (por módulo)

Cada módulo (SaaS e Desktop) segue a mesma estrutura hexagonal. O **domínio** é compartilhado.

```
┌──────────────────────────────────────────────────────────┐
│  Adapters de entrada                                      │
│  SaaS: Web UI (Next.js) · REST API (FastAPI)                 │
│  Desktop: PySide6 (UI + sync + hardware) · PyInstaller .exe │
├──────────────────────────────────────────────────────────┤
│  Camada de aplicação (casos de uso)                       │
│  SaaS: PlanejarDia · GerirProgramas · Analisar · Export…  │
│  Desktop: ExecutarSessao · RegistrarObservacao · Hardware   │
├──────────────────────────────────────────────────────────┤
│  Domínio compartilhado (DDD)                              │
│  Site · Equipamento · ProgramaObservacional (PO-*)        │
│  ProgramaDiario · Sessao · Observacao · ProdutoAnalise    │
│  ContribuicaoRede · regras RN-* · plugins PO-*            │
├──────────────────────────────────────────────────────────┤
│  Portas (interfaces)                                      │
│  ArchivePort · SyncPort · EphemerisPort · MeteoPort       │
│  CameraPort · MountPort · FocuserPort (Desktop)           │
│  ArtifactStorePort · NetworkExportPort                    │
├──────────────────────────────────────────────────────────┤
│  Adapters de saída                                        │
│  SaaS: PostgreSQL · object storage · Astroquery · web     │
│  Desktop: SQLite · filesystem · Alpyca · udrv SBIG        │
└──────────────────────────────────────────────────────────┘
```

---

## 2. Módulos (bounded contexts)

| Módulo | Responsabilidade | SaaS | Desktop |
|--------|------------------|:----:|:-------:|
| `workspace` | Usuário, observatórios, permissões | ✓ | cache |
| `planning` | Efemérides, meteo, programa diário, viabilidade | ✓ | pull |
| `inventory` | Site, equipamento, configuração instrumental | ✓ | ✓ |
| `programs` | Catálogo PO-*, campanhas, prioridades | ✓ | cache |
| `observatory` | Sessão, câmera, montagem, focuser, guiagem | receive | ✓ |
| `reduction` | Calibração, análises, produtos versionados | ✓ | — |
| `archive` | BD + artefatos | mestre | espelho |
| `contribution` | Export / status para redes | ✓ | — |
| `sync` | Pull/push Desktop ↔ SaaS | server | client |
| `shared` | Tempo, IDs, erros de domínio, eventos | ✓ | ✓ |

---

## 3. Persistência

Ver [PERSISTENCIA_E_BANCOS.md](PERSISTENCIA_E_BANCOS.md) e [ARQUITETURA_SAAS_DESKTOP.md](ARQUITETURA_SAAS_DESKTOP.md) §7.

| Módulo | BD | Artefatos |
|--------|-----|-----------|
| **SaaS** | PostgreSQL **BDaaS** (fonte mestre) | Object storage **BDaaS** |
| **Desktop** | SQLite (espelho + fila sync) | Filesystem local |

- Fonte primária de consulta científica: **SaaS** (após sync)
- FITS e plots: storage referenciado por URI no BD
- Sync: [MODELO_DE_SINCRONIZACAO.md](MODELO_DE_SINCRONIZACAO.md)

---

## 4. Relação com sbig-suite

AstroCitizen **não** é fork do sbig-suite.  
Integração no **Desktop**: adapter `CameraPort` → udrv do sbig-suite.  
SaaS **não** acessa hardware.

---

## 5. Princípios

1. UI não importa Alpyca/SQL/Astroquery diretamente.
2. Domínio não conhece frameworks de UI.
3. Novos PO-* = plugin/estratégia, não `if` gigante.
4. Todo caso de uso que gera resultado **persiste no BD** (RN-110).
5. Testes: domínio puro + ports fake + simuladores.
6. **SaaS** não controla hardware; **Desktop** não é fonte mestre de análise/export.
7. Sessão observacional **não depende** do SaaS online (sync offline-first).
8. **Otimização técnica e uso eficiente de recursos** (D-010): menos processos, menos RAM/CPU ociosos, latência mínima no caminho crítico de hardware, sem motores/duplicações injustificadas. Alinhamento a outros produtos não prevalece sobre este princípio.

---

## 6. Documentos relacionados

| Documento | Conteúdo |
|-----------|----------|
| [ARQUITETURA_SAAS_DESKTOP.md](ARQUITETURA_SAAS_DESKTOP.md) | Fronteiras SaaS vs Desktop, deploy, fases |
| [API_ALVO.md](API_ALVO.md) | Contratos REST e ports |
| [MODELO_DE_SINCRONIZACAO.md](MODELO_DE_SINCRONIZACAO.md) | Fila, conflitos, offline |
| [MODELO_DADOS_V1.md](MODELO_DADOS_V1.md) | Schema relacional v1 |
| [COMPARACAO_DESKTOP_TAURI_VS_PYSIDE.md](COMPARACAO_DESKTOP_TAURI_VS_PYSIDE.md) | Desktop PySide6 (D-009.4-rev) |
| [decisoes/D-008-saas-desktop.md](decisoes/D-008-saas-desktop.md) | ADR SaaS+Desktop |
| [decisoes/D-010-otimizacao-recursos.md](decisoes/D-010-otimizacao-recursos.md) | Otimização de recursos |
