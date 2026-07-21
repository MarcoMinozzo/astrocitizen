# Referência ASCOM — AstroCitizen

Espelho local da documentação oficial do [ASCOM Initiative](https://ascom-standards.org/index.htm) (*Astronomy Common Object Model*), organizada para consulta offline durante o desenvolvimento do **módulo Desktop** (hardware via Alpaca/Alpyca).

**Fonte:** https://ascom-standards.org/  
**Espelhado em:** 2026-07-21  
**Arquivos:** 790 OK · 5 indisponíveis (404 no servidor) · ~22 MB  
**Manifesto:** [MANIFEST.json](MANIFEST.json)

---

## Por que esta pasta existe

O AstroCitizen Desktop controla observatório e instrumentos via **ASCOM Alpaca** (HTTP/JSON, multiplataforma) e **Alpyca** (cliente Python). A documentação ASCOM define:

- interfaces de dispositivo (câmera, telescópio, focuser, roda de filtros, condições observacionais…);
- princípios de driver e tratamento de erros;
- referência da API Alpaca;
- especificação das interfaces COM/Alpaca unificadas (*Master Interfaces*).

Ver também: [STACK_TECNOLOGICA.md](../STACK_TECNOLOGICA.md) · [ARQUITETURA_SAAS_DESKTOP.md](../ARQUITETURA_SAAS_DESKTOP.md).

> **Nota 2026 (ASCOM):** novos drivers e aplicações devem priorizar **Alpaca** em detrimento do ASCOM COM clássico (Windows-only). Alpaca usa as mesmas APIs maduras via HTTP/JSON e funciona em Linux e Windows — alinhado ao nosso escopo (D-005, D-006).

---

## Estrutura do espelho

Conteúdo em [`mirror/`](mirror/) — mesma hierarquia do site oficial.

| Pasta | Conteúdo | Relevância AstroCitizen |
|-------|----------|-------------------------|
| [`mirror/newdocs/`](mirror/newdocs/) | **Master Interfaces** (Sphinx) — câmera, telescópio, focuser, dome, filter wheel, observing conditions… | **Alta** — contratos das portas de hardware |
| [`mirror/AlpacaDeveloper/`](mirror/AlpacaDeveloper/) | Desenvolvimento Alpaca, princípios, async, referência API | **Alta** |
| [`mirror/library/html/`](mirror/library/html/) | Documentação gerada das interfaces e clientes Alpaca (.NET) | **Alta** — detalhe de propriedades/métodos |
| [`mirror/help/html/`](mirror/help/html/) | Exceções, utilitários, tipos base ASCOM | Média |
| [`mirror/About/`](mirror/About/) | Visão geral, Alpaca vs COM, arquitetura modular | Média |
| [`mirror/COMDeveloper/`](mirror/COMDeveloper/) | Desenvolvimento COM clássico (legado Windows) | Baixa (referência) |
| [`mirror/Standards/`](mirror/Standards/) | Processo de padronização ASCOM | Baixa |
| [`mirror/alpyca/alpyca.pdf`](mirror/alpyca/alpyca.pdf) | Documentação Alpyca (Python) | **Alta** |
| [`mirror/newdocs/ascom-interfaces.pdf`](mirror/newdocs/ascom-interfaces.pdf) | PDF das interfaces ASCOM | **Alta** |

---

## Documentos prioritários (leitura rápida)

### Alpaca e stack Python

1. [mirror/index.htm](mirror/index.htm) — página inicial ASCOM  
2. [mirror/About/Conn-Alpaca.htm](mirror/About/Conn-Alpaca.htm) — conectividade Alpaca  
3. [mirror/AlpacaDeveloper/Index.htm](mirror/AlpacaDeveloper/Index.htm) — hub desenvolvedor Alpaca  
4. [mirror/AlpacaDeveloper/ASCOMAlpacaAPIReference.html](mirror/AlpacaDeveloper/ASCOMAlpacaAPIReference.html) — referência API Alpaca  
5. [mirror/alpyca/alpyca.pdf](mirror/alpyca/alpyca.pdf) — Alpyca (cliente Python usado no Desktop)

### Interfaces de dispositivo (newdocs)

| Dispositivo | HTML | Porta AstroCitizen |
|-------------|------|-------------------|
| Câmera | [camera.html](mirror/newdocs/camera.html) | `CameraPort` |
| Telescópio / montagem | [telescope.html](mirror/newdocs/telescope.html) | `MountPort` |
| Focuser | [focuser.html](mirror/newdocs/focuser.html) | `FocuserPort` |
| Roda de filtros | [filterwheel.html](mirror/newdocs/filterwheel.html) | FilterWheel |
| Condições observacionais | [observingconditions.html](mirror/newdocs/observingconditions.html) | `MeteoPort` / condições locais |
| Cúpula | [dome.html](mirror/newdocs/dome.html) | Futuro (E17) |
| Rotador | [rotator.html](mirror/newdocs/rotator.html) | Futuro |
| Cover calibrator | [covercalibrator.html](mirror/newdocs/covercalibrator.html) | Flat/dark cap |

Índice completo: [mirror/newdocs/index.html](mirror/newdocs/index.html)

### Mapeamento portas ? interfaces ASCOM

| Porta AstroCitizen | Interface ASCOM | Versão doc |
|--------------------|-----------------|------------|
| `CameraPort` (Alpaca) | `ICameraV3` / `ICameraV4` | newdocs + library |
| `MountPort` | `ITelescopeV3` / `ITelescopeV4` | newdocs + library |
| `FocuserPort` | `IFocuserV3` / `IFocuserV4` | newdocs + library |
| Filter wheel | `IFilterWheelV2` / `V3` | newdocs |
| Observing conditions | `IObservingConditions` / `V2` | newdocs |
| `CameraPort` (SBIG) | — | udrv SBIG (fora ASCOM) |

---

## Arquivos não baixados (404 no servidor)

| URL relativa | Motivo |
|--------------|--------|
| `AlpacaDeveloper/Alpaca.htm` | Link morto no site |
| `Downloads/PlatDevComponents.htm` | Link morto |
| `FAQs/TheSky.htm` | Link morto |
| `help/platform/index.html` | Removido / movido |
| `help/platform/html/P_ASCOM_DeviceInterface_ICameraV3_Gains.htm` | Removido / movido |

Equivalentes provavelmente em `newdocs/` ou `library/html/`.

---

## Uso offline

Abrir no navegador a partir de:

```text
docs/ascom/mirror/index.htm
docs/ascom/mirror/newdocs/index.html
```

As páginas `newdocs/` referenciam CSS/JS em `_static/` — o **conteúdo textual** está completo; estilos Sphinx podem não carregar offline (limitação do espelho parcial de assets estáticos).

Para navegação curada em português: [INDICE_ASCOM.md](INDICE_ASCOM.md).

---

## Atualização do espelho

Reexecutar o script de espelhamento (ver comentário no `MANIFEST.json` ? campo `source`) ou atualizar manualmente URLs alteradas no site oficial.

Respeitar licença e copyright ASCOM Initiative (1998–2026) — uso interno de desenvolvimento e referência; não redistribuir como produto derivado sem verificar [Initiative/Licensing.htm](mirror/Initiative/Licensing.htm).

---

## Links externos

- Site oficial: https://ascom-standards.org/index.htm  
- Alpyca (PyPI): https://pypi.org/project/alpyca/  
- Fórum desenvolvedores ASCOM: via [Support/Index.htm](mirror/Support/Index.htm)

---

## Mapeamento equipamento

Ver [MAPEAMENTO_EQUIPAMENTO_ASCOM.md](MAPEAMENTO_EQUIPAMENTO_ASCOM.md) â€” tabela equipamento â†’ interface ASCOM â†’ driver â†’ porta AstroCitizen.
