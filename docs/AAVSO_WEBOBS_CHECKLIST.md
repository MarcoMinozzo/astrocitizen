# Checklist AAVSO WebObs (PO-A01)

Validar o export Extended gerado pelo AstroCitizen antes de confiar no fluxo de campo.

## Pre-requisitos

1. Conta AAVSO + **Observer Code** (`OBSCODE`)
2. Alvo com fotometria no AstroCitizen (`analysis_products` + `measurement_points`)
3. Carta/sequencia VSP quando aplicavel (`--` chart no futuro; hoje `NA`)

## Gerar ficheiro

```bash
astrocitizen contribute credentials set --network aavso --obscode SEUCODIGO
astrocitizen contribute aavso \
  --product <uuid-do-produto> \
  --star "SS CYG" \
  --band V \
  --out ~/aavso_sscyg.txt
```

Ou equivalente: `astrocitizen analyze export-aavso ...`

## Verificar o ficheiro

- Cabecalho contem `#TYPE=EXTENDED`, `#OBSCODE=...`, `#DATE=JD`, `#OBSTYPE=CCD`
- Cada linha: `STARID,JD,MAG,MERR,FILTER,...` com JD numerico (~2460xxx)
- Abrir em editor e confirmar encoding UTF-8 / ASCII

## Upload WebObs

1. Abrir https://www.aavso.org/webobs/
2. Escolher submit photometric / Extended file
3. Carregar o `.txt` gerado
4. Confirmar aceitacao / corrigir erros do parser AAVSO
5. Guardar o ID/ack no `network_submissions` (ja criado no passo CLI)

## Limites actuais (MVP)

- Sem API de upload automatica (revalidar WebObs 2.0)
- JD a partir de `t_utc` dos measurement_points (nao HJD)
- Comp/check/airmass ainda `na` / ENSEMBLE

## DoD deste checklist

- [ ] Ficheiro aceite pelo WebObs sem erros de formato
- [ ] Pelo menos 1 estrela de teste reportada com OBSCODE real
