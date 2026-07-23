# Checklist AAVSO WebObs (PO-A01 / AC-096)

Validar o export Extended gerado pelo AstroCitizen antes de confiar no fluxo de campo.

## Contrato oficial (fixado)

A AAVSO **nao** disponibiliza API REST publica de **submissao**. O canal suportado e:

```
fotometria → AEF (.txt) validado → upload manual no WebObs → AID
```

Consulta (VSX, VSP, AID download) tem URLs/APIs documentadas; submissao automatizada
via Selenium/POST nao oficial **esta fora de escopo** do AstroCitizen.

## Pre-requisitos

1. Conta AAVSO + **Observer Code** (`OBSCODE`)
2. Alvo com fotometria (`analysis_products` + `measurement_points`)
3. Preferivel carta VSP (`--chart`); default `NA` gera aviso
4. Alvo pode ser resolvido com `target add --name "SS Cyg" --resolve-vsx` (AUID/tipo)

## Gerar ficheiro

```bash
astrocitizen contribute credentials set --network aavso --obscode SEUCODIGO
astrocitizen contribute aavso \
  --product <uuid-do-produto> \
  --star "SS CYG" \
  --band V \
  --chart NA \
  --out ~/aavso_sscyg.txt \
  --open-webobs
```

GUI: **Contribuir → AAVSO → Gerar AEF e preparar WebObs**, depois **Abrir WebObs** /
**Abrir ficheiro AEF**.

Ou: `astrocitizen analyze export-aavso ...`

## Verificar o ficheiro

- Cabecalho contem `#TYPE=EXTENDED`, `#OBSCODE=...`, `#DATE=JD`, `#OBSTYPE=CCD`
- Cada linha: `STARID,JD,MAG,MERR,FILTER,...` com JD numerico (~2460xxx)
- Abrir em editor e confirmar encoding UTF-8 / ASCII
- STARID preferivel = AUID VSX quando disponivel

## Upload WebObs

1. Abrir https://www.aavso.org/webobs/ (botao GUI / `--open-webobs`)
2. Escolher submit photometric / Extended file
3. Carregar o `.txt` gerado
4. Confirmar aceitacao / corrigir erros do parser AAVSO
5. Guardar o ID/ack no `network_submissions` (ja criado no passo CLI/GUI)

## Limites actuais

- Sem API de upload automatica (nao inventar; revalidar WebObs 2.0 se documentarem)
- JD a partir de `t_utc` dos measurement_points (**nao HJD**)
- Comp/check/airmass ainda `na` / ENSEMBLE
- Campanhas AAVSO: browser embutido (AC-095), nao substitui AEF

## DoD deste checklist

- [ ] Ficheiro aceite pelo WebObs sem erros de formato
- [ ] Pelo menos 1 estrela de teste reportada com OBSCODE real
