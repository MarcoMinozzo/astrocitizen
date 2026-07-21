# Compara��o Desktop � Tauri+sidecar vs alternativas

**Vers�o:** 1.0  
**Data:** 2026-07-21  
**Status:** revis�o da D-009.4 (Desktop)  
**Relacionados:** [AVALIACAO_STACK_MOTORSPORT.md](AVALIACAO_STACK_MOTORSPORT.md) � [decisoes/D-009-stack-motorsport-bdaas.md](decisoes/D-009-stack-motorsport-bdaas.md)

---

## 1. Pergunta

> Devemos usar **Tauri + sidecar Python** no Desktop, ou existe solu��o melhor em termos t�cnicos, custo de computa��o, etc.?

## 2. Veredito

| Crit�rio | Vencedor |
|----------|----------|
| Adequa��o ao dom�nio (hardware + Astropy + FITS) | **PySide6 (app Python �nica)** |
| Custo de CPU/RAM em sess�o noturna | **PySide6** (um processo) |
| Complexidade de empacote / falhas | **PySide6** |
| Reuso do padr�o sync do motorsport | Tauri (mas o sync � facilmente replic�vel em Python) |
| UI partilhada com SaaS (React) | Tauri / web |
| **Recomenda��o AstroCitizen Desktop** | **PySide6 como shell principal** |

**Tauri + sidecar** continua v�lido como *padr�o de plataforma* no motorsport (sync de ficheiros, pouco dom�nio nativo). No AstroCitizen o dom�nio **vive em Python**; o sidecar vira o verdadeiro app e o Tauri torna-se casca cara.

Recomenda��o revista:

```text
SaaS (inalterado D-009.1�3):  FastAPI + Next.js + Postgres/object BDaaS
Desktop (revis�o D-009.4):    PySide6 + Python (dom�nio + hardware + sync)
Opcional P3:                  Agente Tauri �tray-only� se quiserem app m�nima sempre ligada
```

---

## 3. O que o Desktop precisa fazer

| Fun��o | Peso | Stack natural |
|--------|------|----------------|
| Controlo c�mera/montagem/foco | Cr�tico | Python (Alpyca, udrv) |
| Sess�o, preview FITS, cooler | Cr�tico | Python + Qt / imagem |
| Efem�rides locais, headers | Alto | Astropy |
| Sync offline ? SaaS | Alto | HTTP + SQLite (qualquer linguagem) |
| Tray / autostart | M�dio | Qt ou Tauri |
| UI id�ntica ao Next.js | Baixo | Nice-to-have, n�o requisito |

~80�90% do valor e do risco est� no **runtime Python**. A shell UI � secund�ria.

---

## 4. Alternativas comparadas

### A � Tauri 2 + sidecar Python (D-009 original)

```text
[Tauri React+Rust] --IPC/HTTP--> [Python observatory-runtime]
         |                                    |
      sync/auth                          Alpyca/udrv/Astropy
```

| Pr�s | Contras |
|------|---------|
| Reusa experi�ncia motorsport | **Dois runtimes** sempre (WebView + Python) |
| UI React alinhada ao SaaS | IPC: versionamento, ports, crashes �rf�os |
| Tray/Rust eficiente para sync | Empacote: instalador Tauri **+** runtime Python |
| | Debug e CI mais caros |
| | Tauri n�o acelera o caminho cr�tico (hardware) |

**Custo t�pico (ordem de grandeza):** WebView+Rust idle ~80�150 MB + Python/Astropy/Qt ou headless ~150�300 MB ? **230�450 MB** e dois GC/schedulers.

### B � PySide6 monol�tico (recomendado)

```text
[PySide6 UI + domain + hardware + sync client]
              |
         SQLite local + FITS
              |
         Sync API ? SaaS
```

| Pr�s | Contras |
|------|---------|
| **Um processo, uma linguagem** | UI n�o � React (dois design systems) |
| Continuidade do **sbig-suite** | Reimplementar fila sync (baixo esfor�o vs sidecar) |
| Astropy/Alpyca/udrv no mesmo address space | Bundle PyInstaller/Nuitka maior em disco |
| Empacote j� conhecido | Tray/autostart menos �moderno� que Tauri |
| Menos falhas de IPC | |

**Custo t�pico:** um processo Python+Qt+Astropy ~**150�280 MB** em sess�o; idle menor.

### C � Electron + Python sidecar

Pior que A em RAM/CPU (Chromium). **Rejeitada.**

### D � Dois apps (Tauri sync + PySide observat�rio)

| Pr�s | Contras |
|------|---------|
| Separa��o limpa | Dois instaladores, UX partida |
| | Utilizador confuso (�qual abro � noite?�) |

S� faz sentido se no futuro houver �agente leve� + �console pesado� como produtos distintos.

### E � S� web (browser) + agente m�nimo

Invi�vel para slew/exposi��o em tempo real e offline de campo sem agente local robusto.

### F � Tauri-only (hardware em Rust)

Reescrever udrv/Alpyaca/Astropy. **Custo proibitivo.** Rejeitada.

---

## 5. Custo de computa��o e opera��o

| M�trica | Tauri + sidecar | PySide6 �nico |
|---------|-----------------|---------------|
| Processos | 2+ | 1 |
| RAM sess�o | Maior | Menor |
| CPU idle | WebView + Python | S� Python/Qt |
| Lat�ncia hardware | IPC + GIL | Chamada directa |
| Cold start | Dois boots | Um boot |
| Falha t�pica | Sidecar morreu, UI �viva� sem c�mera | Crash �nico (mais simples de diagnosticar) |
| Tamanho instalador | Tauri + Python embutido | PyInstaller (grande, mas um artefacto) |
| Manuten��o equipa | Rust + TS + Python | Python (+ QML/Qt se avan�ado) |

Em PC de observat�rio (muitas vezes modestos, noite longa, cooler ligado): **menos processos = melhor**.

O sync do motorsport � I/O-bound (ficheiros). O Desktop AstroCitizen � **control-bound** (USB, HTTP Alpaca, readout). Opcional Tauri n�o reduz o trabalho pesado.

---

## 6. Custo de desenvolvimento (equipa)

| Item | Tauri+sidecar | PySide6 |
|------|---------------|---------|
| Partir do sbig-suite | Baixo reaproveitamento UI | **Alto** |
| Fila offline + JWT | J� no Tauri | ~1�2 sprints Python (`httpx`, `aiosqlite`) |
| CameraPort / sess�o | Sidecar (igual) | In-process (mais simples) |
| Partilhar componentes React com SaaS | Sim | N�o (s� contratos API) |
| Curva aprendizagem | 3 stacks | 1 stack + Qt |

Contratos SaaS (`API_ALVO`, sync batch) **n�o dependem** de Tauri � qualquer cliente HTTP serve.

---

## 7. Quando Tauri ainda faria sentido

1. Produto �**s� agente de sync**� (importar FITS de pasta, sem controlo de montagem) � an�logo motorsport.  
2. Equipa quer **um �nico design system React** web+desktop a todo o custo.  
3. Fase P3: tray agent m�nimo enquanto o console PySide est� fechado.

Para o **console de observat�rio** do mandato actual (PO-*, sess�o, SBIG, Alpaca): **n�o � a melhor op��o t�cnica**.

---

## 8. Decis�o proposta (substitui D-009.4)

| # | Decis�o |
|---|---------|
| D-009.4-rev | Desktop principal = **PySide6 + Python** (UI, dom�nio, hardware, sync client). |
| D-009.4b | Sync offline = SQLite + cliente HTTP no mesmo processo (espelhar comportamento do Tauri motorsport, n�o a implementa��o Rust). |
| D-009.4c | Tauri = **opcional / futuro**, n�o caminho cr�tico do MVP Desktop. |
| D-009.1�3 | SaaS (FastAPI, Next.js, BDaaS) **mant�m-se**. |

### Arquitectura alvo revista

```text
???????????????????????????????????????????????
?         AstroCitizen Desktop (PySide6)      ?
?  UI � Planejar local � Sess�o � Preview     ?
?  CameraPort / MountPort / FocuserPort       ?
?  SyncClient (fila SQLite ? SaaS)            ?
???????????????????????????????????????????????
                       ? HTTPS Sync API
                       ?
???????????????????????????????????????????????
?  AstroCitizen SaaS (FastAPI + Next.js)      ?
?  PostgreSQL BDaaS � Object storage BDaaS    ?
???????????????????????????????????????????????
```

---

## 9. Crit�rios de aceite desta revis�o

1. Documenta��o deixa de apresentar Tauri+sidecar como caminho obrigat�rio do Desktop.  
2. PRODUCT_BACKLOG / E7: GUI shell = PySide6 (como AC-071 original).  
3. SaaS permanece Next.js (React s� no browser).  
4. Sync Desktop especificado a n�vel de protocolo (`API_ALVO`), n�o de framework UI.

---

## 10. Hist�rico

| Vers�o | Data | Notas |
|--------|------|-------|
| 1.0 | 2026-07-21 | Revis�o: PySide6 prefer�vel a Tauri+sidecar para observat�rio |

---

## 11. Requisito de produto — executável Windows

No final do dia o Desktop tem de existir como **binário Windows que funciona bem**:

| Critério | Detalhe |
|----------|---------|
| Forma | `AstroCitizen.exe` (ou instalador que o inclui) |
| Runtime | Sem Python no PATH do utilizador |
| Empacote | PyInstaller (baseline sbig-suite); onedir se onefile for lento no arranque |
| CI | Build em `windows-latest` + smoke (`--backend simulator` / CLI mínima) |
| Hardware | DLL/drivers SBIG e Alpaca **fora** do `.exe` (documentar no README) |
| Qualidade | Arranque estável, GUI abre, sessão simulada, sem crashes triviais |

Isto é **não negociável** na escolha de stack Desktop. PySide6 cumpre via o mesmo padrão já usado no sbig-suite.
