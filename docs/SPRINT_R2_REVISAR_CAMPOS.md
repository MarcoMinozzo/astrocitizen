# Sprint R2 — Contribuir: Revisar campos (AAVSO / MPC)

**Data:** 2026-07-23  
**Estado:** concluido (slice AAVSO+MPC)  
**Depende:** AC-141, D-011, atlas ATLAS_REPORTE

## Entregas

1. Helpers `prefill_aavso_fields` / `prefill_mpc_fields` (produto + credenciais)
2. Dialogo GUI **Revisar campos** nas tabs AAVSO e MPC
3. Verificar AC-141 no dialogo; Aceitar grava `NetworkSubmission` `draft`
4. Tab MPC: Product UUID + mag/band; export passa `product_id` a validacao
5. AAVSO: campo Chart no formulario e no export Extended

## Fora deste slice

- Revisar campos para TNS / BeSS / ExoClock / IOTA (R3)
- WDS — feito em [SPRINT_EXP_WDS.md](SPRINT_EXP_WDS.md)
- Upload WebObs automatico
- ADES XML
- COBS

## DoD

- [x] Prefill do produto (MPC espelha CLI; AAVSO via params/target)
- [x] Validacao bloqueia Aceitar com erros
- [x] Rascunho aparece na lista de envios
- [x] Testes unitarios dos helpers
