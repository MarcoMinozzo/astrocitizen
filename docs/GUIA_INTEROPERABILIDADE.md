# Guia de interoperabilidade — AstroCitizen

Resumo normativo da correção de rota (fonte completa externa:
`moodle_espectroscopia/guia_astrocitizen.md`). Nome de produto: **AstroCitizen**.
Arquitectura: [D-012](decisoes/D-012-hub-integrations.md) ·
[D-013](decisoes/D-013-espelho-formularios-info.md) ·
épico guarda-chuva [E22](EPICO_E22_HUB_CIENTIFICO.md) ·
UX [UX_E22](UX_E22_INTEROPERABILIDADE.md).

## Ideia central

Observatório de pequeno/médio porte → hub que **consulta catálogos** e
**publica** fotometria / espectro / astrometria / transientes via providers
pluggáveis — sem inventar APIs privadas.

Além do hub externo, a plataforma:

1. **Espelha** todas as observações/submissões no **SaaS próprio** (BD mestre).
2. Usa **formulários** versionados compatíveis com cada API (atlas).
3. Expõe **serviços de informação internos** sobre cache nosso dos dados
   institucionais (VSX, SIMBAD, …) e o **catálogo próprio** (ficha unificada);
   sem browse raw do `institutional_cache`.
4. **Controla hardware** no Desktop via **ASCOM Alpaca** (câmara, telescópio,
   focuser; depois filter wheel / condições / dome) — épico E4; não confundir
   com `integrations/` de redes. Ver [ascom/README.md](ascom/README.md).

Ver [D-013](decisoes/D-013-espelho-formularios-info.md).

## Matriz A–E (resumo)

| Grupo | Papel | Exemplos | UI de produto |
|-------|--------|----------|---------------|
| **A** Consumo | Nome → coords / mag / tipo → cache | Sesame, SIMBAD, VSX, VizieR, Gaia | Nenhuma (efeitos em Noite/Alvos) |
| **B** Publicação | Artefacto oficial | AAVSO, BeSS, MPC, TNS, ARAS | Contribuir |
| **C** Alertas | Candidatos | ALeRCE, Lasair | Inbox → Noite (Fase 3) |
| **D** Arquivos | Referência | MAST, ESO | Analisar (Fase 4) |
| **E** Ops | Meteo / solve / hardware | Open-Meteo, Astrometry, ASCOM | Noite / Observar |

Tabela completa e inventário pronto/lacuna: [EPICO_E22_HUB_CIENTIFICO.md](EPICO_E22_HUB_CIENTIFICO.md).
Wireframes: [UX_E22_INTEROPERABILIDADE.md](UX_E22_INTEROPERABILIDADE.md).

## Fases

| Fase | Foco | Integrações |
|------|------|-------------|
| **1** Base científica | **Consumo → cache → agenda**: Sesame, SIMBAD, VSX (VizieR/Gaia a seguir); AAVSO fotometria (consulta + AEF/WebObs) |
| **2** Espectroscopia | ARAS, BeSS, AAVSO Spectroscopy |
| **3** Transientes | TNS, ALeRCE, Lasair |
| **4** Arquivos | MAST, ESO Archive |
| **5** Automação | alertas→plano, comparação histórica, one-click publish |

### Fase 1 — consumo → cache → agenda (slice actual)

Prioridade desta fase **não** é publicar mais formatos; é:

1. **Consumir** catálogos (Sesame coords → VSX AUID/tipo/período/mag → SIMBAD fallback).
2. **Organizar** em `institutional_cache` + `Target.external_ids` (**store interno**).
3. **Consultar** offline via CLI (`catalog resolve|refresh-targets|cache-*`) — diagnóstico; não é UX principal.
4. **Alimentar** `GenerateDailyPlan` / ProgramaDiario com notas de catálogo e
   tie-break por `mag_max` quando a prioridade de programa empatar
   (geração **sem rede**; refresh prévio é explícito).

Serviço: `CatalogResolveService` (`integrations/catalog_service.py`) · AC-226 / AC-211.  
Coordenação: **E22** (AC-230…234).

**Paralelo (obrigatório, não opcional):** **ASCOM Alpaca** (E4 — aquisição),
Astrometry.net, JPL Horizons, meteo, client IVOA TAP. INDI fica como opção
secundária se necessário no ecossistema Linux.

## Top 20 (checklist longo prazo)

1. SIMBAD · 2. VizieR · 3. Gaia · 4. CDS X-Match · 5. Sesame  
6. AAVSO · 7. ARAS · 8. BeSS · 9. TNS · 10. MPC  
11. JPL Horizons · 12. Astrometry.net · 13. ALeRCE · 14. Lasair  
15. MAST · 16. ESO · 17. ASCOM Alpaca · 18. INDI  
19. CelesTrak · 20. Meteoblue / meteo astronómico  

Multiplicador: padrões **IVOA** (TAP, SIA, SSA, Cone Search, VOEvent).

## Modelo interno (não formato institucional)

- `Observation` — id, object_name, ra, dec, jd, observer, observatory_code, instrument, filter, exposure, snr  
- `Spectrum` — wavelength[], flux[], uncertainty[], resolution, fits_header  

Cada provider converte para o destino (AEF, BeSS FITS, ADES, TNS JSON, …).

## Estado no repo (slice skeleton)

| Provider | features (manifesto) | Backend actual |
|----------|----------------------|----------------|
| Sesame | search | `adapters/sky/sesame_resolver.py` + cache |
| SIMBAD | search | `adapters/sky/simbad_resolver.py` + cache |
| VSX | search | `adapters/sky/vsx_resolver.py` + cache |
| VizieR | search | `adapters/sky/vizier_resolver.py` + cache (ASU) |
| Gaia | search | `adapters/sky/gaia_resolver.py` + cache (TAP) |
| AAVSO | search, prepare_photometry | AEF + WebObs (AC-096) |
| MPC | prepare_astrometry | ADES PSV |
| TNS | prepare_transient | AT report |
| BeSS | prepare_spectrum | FITS 1D |

Facade: `CatalogResolveService` (Sesame→VSX→SIMBAD + cone VizieR/Gaia).

Novos clientes (X-Match, …) = E20 / AC-233 · coordenados por **E22**.
Mapa completo: [EPICO_E22_HUB_CIENTIFICO.md](EPICO_E22_HUB_CIENTIFICO.md).
