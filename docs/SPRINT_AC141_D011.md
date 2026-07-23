# Sprint — AC-141 validacao + D-011 ferramentas imagem

**Data:** 2026-07-23  
**Estado:** concluido (slice 1)  
**Decisao:** [D-011-imagem-ferramentas-externas.md](decisoes/D-011-imagem-ferramentas-externas.md)

## Entregas

1. **AC-141** — `validate_product_for_network` (AAVSO, MPC, ExoClock, BeSS, TNS, IOTA, solar, WDS)
2. CLI `contribute validate` + gate em `contribute aavso` / `mpc` (+ GUI AAVSO/MPC)
3. **AC-134 / D-011** — `ImageToolPort` + `ExternalImageToolLauncher`
4. Arquivo: Abrir artefacto → SO / DS9 / Siril / ASTAP
5. Preferencias: comandos `%f` por ferramenta

## Fora deste slice

- UI completa "Revisar campos" — feito em [SPRINT_R2_REVISAR_CAMPOS.md](SPRINT_R2_REVISAR_CAMPOS.md)
- Exporters WDS/COBS
- Suite de processamento embutida (nunca — D-011)

## DoD

- [x] Validacao bloqueia export incompleto (AAVSO/MPC)
- [x] Abrir externo configuravel
- [x] Doc D-011
- [x] Testes
