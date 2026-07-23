# Sprint — AC-079 Carta do céu L0 (painel Noite)

**Data:** 2026-07-23  
**Estado:** concluido  
**Prioridade:** P2  
**Dependencias:** AC-030, AC-034, AC-038, AC-073a  
**Alinhamento:** D-010 (leve), RN-001 (sempre relativo ao Site)

## Entregas

1. `planning/sky_projection.py` — `altaz_to_sky_xy`, modelo `SkyChartModel` (AC-038)
2. `AstropyEphemeris.body_altitude_azimuth` — Sol/Lua
3. `desktop/sky_chart.py` — widget Qt (paint + clique)
4. Painel **Noite**: carta + slider da noite + Agora + detalhe do alvo

## Decisao de produto (L0)

Carta **operacional** dos alvos do ProgramaDiario — **nao** e planetario.  
Fora: catalogo HYG, FOV, Stellarium embutido (ver AC-079b/c).

## DoD

- [x] Widget de carta no painel Noite, ligado ao Site e a data/hora
- [x] Alvos do plano do dia projectados; estados visuais
- [x] Sol + Lua + limiar de altitude
- [x] Controlo de hora (Agora + scrub)
- [x] Clique → detalhe do alvo
- [x] Testes unitarios da projecao + modelo
- [x] Docs sprint + backlog + nota UI
- [x] Sem deps novas alem de PySide6/Astropy ja existentes

## Uso

1. Abrir `astrocitizen gui` → **Noite**
2. Seleccionar site → **Atualizar noite**
3. (Opcional) **Gerar plano** com programas activos / alvos
4. Usar slider / **Agora**; clicar marcadores na carta

## Referencias

- AC-079b L1 catalogo · AC-079c launcher externo
