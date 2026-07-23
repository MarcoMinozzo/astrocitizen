# Politica de conflito (trust tiers)

Quando duas passagens contradizem:

| Dominio | Preferir | Sobre |
|---------|----------|-------|
| Como o produto AstroCitizen funciona (UX, RN, PO workflow) | **T3** | T1 / T2 / T5 |
| Facto fisico / astrofisica | **T1** (depois T2) | T3 / T5 |
| Formato oficial de rede (export) | **T4** (fonte rede) se citado; senao T3 atlas | T5 |
| Dicas praticas / lab | T5 so se nao conflitar com T3 safety/RN | — |

## Regras

1. Nunca inventar procedimentos de redes sem passagem citada.
2. Medidas cientificas (fotometria, spectrum-report, plate-solve) **nao** sao substituidas por RAG.
3. Em conflito UX vs paper: docs da plataforma ganham para “como usar o software”.
4. Em conflito ciencia: paper/manual > copy interno generico.
5. Sempre devolver `source_id`, `chunk_id`, `trust_tier` ao consumidor.
