# D-012 — Hub de interoperabilidade (integrations / ObservatoryProvider)

**Data:** 2026-07-23  
**Estado:** aceite  
**Contexto:** correção de rota segundo o guia de interoperabilidade
([GUIA_INTEROPERABILIDADE.md](../GUIA_INTEROPERABILIDADE.md); fonte externa
`guia_astrocitizen.md`). O produto permanece **AstroCitizen** (não renomear
para AstroDART).

## Decisão

1. AstroCitizen é um **hub de integrações** científicas (consulta + publicação),
   não um silo acoplado a um único formato institucional.
2. O domínio usa modelos canónicos (`Observation`, `Spectrum`); **nunca**
   persiste AEF/ADES/TNS JSON como modelo interno.
3. Cada instituição implementa `ObservatoryProvider` em `integrations/<rede>/`
   com manifesto `features` (search, upload_photometry, …).
4. Submissão usa o **canal oficial** de cada rede (ficheiro+WebObs, REST, ADES,
   FITS BeSS, …). **Selenium / scraping não é caminho principal.**
5. IVOA (TAP, Cone Search, …) entra como facade genérica (Fase 1b+) para
   multiplicar catálogos sem um adapter por serviço.
6. Migração **incremental**: `contribution/` continua válido; wrappers em
   `integrations/` delegam até a lógica migrar por completo.

## Camadas

```text
Observação (FITS/RAW)
  → Processamento (redução / análise)
  → Observation / Spectrum (domínio)
  → integrations.registry (providers)
       → AAVSO | MPC | TNS | BeSS | SIMBAD | …
```

## Anti-padrões

- Formato AAVSO Extended / MPC80 / TNS no domínio ou BD
- Upload “automágico” não documentado pela instituição
- Reescrever toda a GUI ou as 20 APIs de uma vez
- Depender de SaaS para o DoD Desktop

## Relacionados

- D-007 atlas de reporte · D-010 recursos · D-011 ferramentas externas  
- Épico **E20** no PRODUCT_BACKLOG  
- Código: `ports/observatory_provider.py`, `domain/observation.py`, `integrations/`
