# Sprint — AC-197 MCP read-only KB tools

**Data:** 2026-07-23  
**Estado:** concluido  
**Depende:** AC-194 / AC-195

## Entregas

1. `knowledge/mcp_tools.py` — `kb_search`, `kb_get_chunk`, `kb_list_sources` + rate limit
2. JSON-RPC MCP subset (`initialize`, `tools/list`, `tools/call`, `ping`)
3. CLI:
   - `knowledge mcp-tools`
   - `knowledge mcp-call <tool> --arguments '{...}'`
   - `knowledge mcp-serve` (stdio, linha a linha)

## Fora deste slice

- Glossario MCP `kb_get_glossary` (AC-198)
- Assistente Ajuda GUI (AC-196)
- SDK oficial `mcp` package (opcional)

## DoD

- [x] Tools read-only com citacoes
- [x] Rate limit por processo
- [x] Invocavel via CLI sem servidor externo
- [x] Testes AC-197
