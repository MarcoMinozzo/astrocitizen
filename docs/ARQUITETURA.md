# Arquitetura — AstroCitizen

**Decisão:** monólito modular + arquitetura hexagonal (Ports & Adapters) + DDD + plugins PO-*  
**Data:** 2026-07-21  
**Status:** especificação

---

## 1. Forma do sistema

```
┌──────────────────────────────────────────────────────────┐
│  Adapters de entrada                                      │
│  GUI (PySide6) · CLI · (futuro) API local                 │
├──────────────────────────────────────────────────────────┤
│  Camada de aplicação (casos de uso)                       │
│  PlanejarDia · ExecutarSessao · RegistrarObservacao       │
│  Analisar · GerirProgramas · ExportarRede                 │
├──────────────────────────────────────────────────────────┤
│  Domínio (DDD)                                            │
│  Site · Equipamento · ProgramaObservacional (PO-*)        │
│  ProgramaDiario · Sessao · Observacao · ProdutoAnalise    │
│  ContribuicaoRede · regras RN-*                           │
│  Plugins por técnica / template PO-*                      │
├──────────────────────────────────────────────────────────┤
│  Portas (interfaces)                                      │
│  EphemerisPort · MeteoPort · CameraPort · MountPort       │
│  FocuserPort · ArchivePort · ArtifactStorePort            │
│  NetworkExportPort · ObservingConditionsPort              │
├──────────────────────────────────────────────────────────┤
│  Adapters de saída                                        │
│  Astropy/Astroquery · API meteo · Alpyca                  │
│  SBIG udrv (via integração sbig-suite ou binding)         │
│  SQL (SQLite→PostgreSQL) · filesystem FITS                │
│  Exporters AAVSO/MPC/IOTA/ARAS                            │
└──────────────────────────────────────────────────────────┘
```

---

## 2. Módulos (bounded contexts)

| Módulo | Responsabilidade |
|--------|------------------|
| `planning` | Efemérides, meteo, programa diário, viabilidade |
| `inventory` | Site, equipamento, configuração instrumental |
| `programs` | Catálogo PO-*, campanhas, prioridades |
| `observatory` | Sessão, câmera, montagem, focuser, guiagem |
| `reduction` | Calibração, análises, produtos versionados |
| `archive` | BD + artefatos |
| `contribution` | Export / status para redes |
| `shared` | Tempo, IDs, erros de domínio, eventos |

---

## 3. Persistência

Ver [PERSISTENCIA_E_BANCOS.md](PERSISTENCIA_E_BANCOS.md).

- Fonte primária de consulta: **banco de dados**
- FITS e plots: storage referenciado por URI no BD
- Início: SQLite · Evolução: PostgreSQL via mesma `ArchivePort`

---

## 4. Relação com sbig-suite

AstroCitizen **não** é fork do sbig-suite.  
Integração futura: adapter `CameraPort` que delega ao backend udrv do sbig-suite, ou biblioteca extraída.  
Até lá, domínio/BD/planejamento usam **simuladores**.

---

## 5. Princípios

1. UI não importa Alpyca/SQL/Astroquery diretamente.
2. Domínio não conhece frameworks de UI.
3. Novos PO-* = plugin/estratégia, não `if` gigante.
4. Todo caso de uso que gera resultado **persiste no BD** (RN-110).
5. Testes: domínio puro + ports fake + simuladores.
