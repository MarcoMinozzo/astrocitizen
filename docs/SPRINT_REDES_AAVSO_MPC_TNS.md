# Sprint redes P1 — AAVSO + MPC + TNS

**Data:** 2026-07-21  
**Meta:** contributo multi-rede usavel (export + submit dry-run / real opcional)  
**PO-* alvo:** A01 (AAVSO), C01/C02 (MPC ADES), C03 (TNS)

## DoD deste sprint

1. **AAVSO Extended** com JD (Astropy) + CLI; submit = ficheiro pronto para WebObs (API upload ainda nao oficial)
2. **MPC ADES PSV** minimo + `submit_psv` HTTP (default `--dry-run`)
3. **TNS AT-rep JSON** + cliente sandbox (default `--dry-run`)
4. Credenciais locais em `~/.astrocitizen/credentials.json` (nao no SQLite)
5. Tabela `network_submissions` (estado draft/submitted/failed/dry_run)
6. Testes com mocks HTTP; sem envio real no CI

## Fora de escopo

- BeSS / ExoClock / IOTA (sprint seguinte)
- Plate-solve / astrometria automatica (MPC usa medidas fornecidas)
- Painel GUI de envios (AC-143)

## Ordem de implementacao

1. Credenciais + modelo submission  
2. AAVSO JD fix  
3. MPC PSV + submit  
4. TNS JSON + sandbox client  
5. CLI `contribute …`  
6. Docs backlog AC-112 / AC-140…142 / AC-093
