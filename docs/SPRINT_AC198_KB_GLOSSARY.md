# Sprint — AC-198 Glossario astro/redes/PO

**Data:** 2026-07-23  
**Estado:** concluido  
**Depende:** AC-192

## Entregas

1. `knowledge-base/glossary.json` — termos piloto (PO, redes, spectrum_report, …)
2. `knowledge/glossary.py` — lookup / search / `sync_glossary_chunks`
3. CLI `knowledge glossary list|get|sync`
4. MCP tool `kb_get_glossary`
5. Chunks `glossary-*.md` + entrada no catalog

## Fora deste slice

- UI Desktop dedicada ao glossario (usa Help/ask por agora)
- Traducao completa es/en de cada termo

## DoD

- [x] Glossario versionado no KB
- [x] Sync → chunks citaveis
- [x] Lookup CLI + MCP
- [x] Testes AC-198
