# Estudo / backlog — AC-079 Carta do céu L0 (painel Noite)

**Data:** 2026-07-23  
**Estado:** proposto (sem implementacao)  
**Prioridade:** P2  
**Estimativa:** M (~1–2 semanas)  
**Dependencias:** AC-030, AC-034, AC-073a  
**Alinhamento:** D-010 (leve), RN-001 (sempre relativo ao Site)

## Problema

O planeamento ja calcula AltAz / viabilidade, mas o utilizador so ve tabelas. Falta uma **vista espacial operacional** dos alvos do ProgramaDiario no horizonte do Site.

## Decisao de produto (L0)

**Fazer:** carta operacional embutida no painel **Noite** (e reutilizavel depois em Programa activo).  
**Nao fazer neste item:** planetario completo, catalogo HYG/Gaia, FOV optico, satelites, WebView Aladin, embutir Stellarium.

Niveis futuros (fora do DoD deste AC):

| ID futuro | Nivel | Notas |
|-----------|-------|-------|
| AC-079b | L1 catalogo leve | Estrelas brilhantes + constelacoes (opt-in / extra) |
| AC-079c | L3 launcher | Abrir Stellarium/KStars com site+hora+alvo |

## Escopo L0

### Entradas
- Site activo (lat, lon, alt)
- Instante: “agora” + slider/hora ao longo da noite do plano
- Alvos / blocos do ProgramaDiario da data
- Limiar de altitude minima do programa (se existir; senao default documentado, ex. 25°)
- Sol e Lua (posicao AltAz via `EphemerisPort`)

### Vista
- Projecao **zenith / polar azimutal** (zenith no centro, horizonte no bordo) **ou** disco equivalente
- Norte marcado; azimute legivel
- Marcadores dos alvos do plano (cor/estado: acima / abaixo limiar / inviavel_ceu)
- Sol e Lua distintos
- Circulo (ou anel) da altitude minima
- Clique num alvo → selecciona / mostra detalhe do bloco (ligacao a lista do plano)
- Offline: sem rede obrigatoria (so Astropy + dados locais)

### Fora de escopo L0
- Catalogo estelar de fundo
- Pan/zoom estilo planetario
- `horizon_mask` poligonal do site (pode ser AC seguinte; L0 usa horizonte ideal)
- Sync com montagem (ponteiro “onde aponta”)
- Empacote de tiles / DuckDB / starplot como dependencia obrigatoria

## Abordagem tecnica recomendada

1. **Nucleo puro:** funcao `altaz_to_sky_xy(alt, az) -> (x, y)` + modelo de pontos (testavel sem GUI).
2. **Widget Qt:** `QWidget`/`QGraphicsView` com `paintEvent` (stdlib PySide6; sem WebEngine).
3. **Efemerides:** reutilizar `AstropyEphemeris` / `EphemerisPort` (AC-030); nao duplicar matematica.
4. **Starplot:** opcional mais tarde para “exportar PNG da carta”; **nao** dependencia do MVP L0 (D-010 / tamanho `.exe`).

## DoD

- [ ] Widget de carta no painel Noite, ligado ao Site e a data/hora
- [ ] Alvos do plano do dia projectados; estados visuais coerentes com o diario
- [ ] Sol + Lua + limiar de altitude
- [ ] Controlo de hora (agora + scrub da noite)
- [ ] Clique → feedback no plano / detalhe do alvo
- [ ] Testes unitarios da projecao + smoke com site+alvos sinteticos (sem display se possivel)
- [ ] Docs: este sprint + nota em WORKFLOWS / DESKTOP_UI (mapa = vista do plano, nao planetario)
- [ ] Sem regressao no painel Noite existente (meteo/radar/gerar plano)
- [ ] Extra `[gui]` sem novas deps pesadas obrigatorias

## Riscos

| Risco | Mitigacao |
|-------|-----------|
| Parecer “Stellarium incompleto” | Copy: “Carta do plano”; L3 externo depois |
| Performance scrub | Recalcular so pontos do plano (N pequeno), nao catalogo |
| Polar vs hemisferio | Testes com site BR (lat < 0) e EU |
| `.exe` | Sem catalogos grandes no L0 |

## Ordem de implementacao sugerida (quando SIM)

1. Modulo `planning/sky_projection.py` + testes  
2. Widget `desktop/sky_chart.py`  
3. Integrar em `night.py`  
4. Docs + checklist DoD  

## Referencias internas

- Estudo conversacional 2026-07-23 (niveis L0–L3)
- AC-073a painel Noite
- AC-030 EphemerisPort
- D-010 / D-011 (preferir leve + externo para suites pesadas)
