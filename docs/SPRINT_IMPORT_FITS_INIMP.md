# Sprint — Import FITS (IN-IMP)

**Data:** 2026-07-22  
**Estado:** concluido

## Entregas

- Dominio `ImportFits` + `discover_fits_paths`
- CLI `astrocitizen import fits --path …`
- GUI nav **Import** (ficheiro/pasta, site, programa, IMAGETYP)
- Observation `state=imported`, artifact `fits_imported`
- Docs: ENTRADA_OBSERVACOES_POR_PO + AC-054 inicio

## Uso

```bash
astrocitizen import fits --path ./night/ --site Casa --frame-type light
```

## Limites

- So FITS (.fits/.fit/.fts); SER/CSV/radio noutro sprint
- Associacao a programa e por UUID/combo (sem wizard completo)
