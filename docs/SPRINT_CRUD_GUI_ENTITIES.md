# Sprint — CRUD GUI Site / Programa / Alvo

Evolucao AC-072: formularios Novo/Editar/Remover nas paginas Sites, Programas e Alvos.

## Entregas

| Item | Detalhe |
|------|---------|
| Modulo | `desktop/entities.py` |
| Nav | Nova entrada **Alvos** |
| Sites | lat/lon/elev/tz/alt min/default |
| Programas | template PO-* (seed), estado, prioridade |
| Alvos | designacao, RA/Dec, tipo, ligacao opcional a programa |
| Archive | `soft_delete_target` |

## Fluxo seguinte

Wizard **Sessao** (IN-CAP) — captura com site/programa/alvo ja cadastrados.

## Checklist

- [x] CRUD Sites / Programas / Alvos
- [x] soft_delete_target
- [x] Testes archive
- [x] Wizard Sessao
