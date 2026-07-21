# Sprint — PO-E03 Sol / manchas (AC-088)

**Data:** 2026-07-21  
**Estado:** concluido

## Entregas

| Item | Detalhe |
|------|---------|
| Workflow | `PO-E03` em `P1_WORKFLOWS` (safety ? acquire ? count ? export) |
| Analise | `analyze sunspots` com checklist de seguranca obrigatorio |
| Contagem | Deteccao esqueleto + override manual; Wolf `R=k*(10g+s)` |
| Export | `contribute solar` ? texto `#TYPE=ASTROCITIZEN_SOLAR` |
| Safety | Inicio AC-132: filter / no eyepiece unfiltered / daytime ack |

## Aviso

Observacao solar **sem filtro certificado e perigosa**. A CLI exige os tres flags de confirmacao antes de qualquer analise.

## Uso

```bash
astrocitizen analyze sunspots --fits-uri file://... \
  --filter-confirmed --no-unfiltered-eyepiece --daytime-ack \
  --filter-name white-light --spots 5 --groups 2

astrocitizen contribute solar --product <id> --out sunspot.txt
```

## Limites

- Deteccao automatica e heuristica (nao substitui contagem visual cuidadosa).
- Sem exporter especifico SILSO/AAVSO Solar ainda (formato arquivo local).
- Sem GUI dedicada nesta sprint.

## DoD

- [x] Workflow + produto `solar_sunspots`
- [x] Checklist bloqueante
- [x] CLI + testes
- [x] Backlog AC-088 / AC-132 inicio
