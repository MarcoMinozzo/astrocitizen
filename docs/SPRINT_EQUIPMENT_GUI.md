# Sprint — Equipamento + Setup instrumental (GUI)

Fecha AC-072: inventario de equipamento e ConfiguracaoInstrumental na desktop, com atribuicao a Programa.

## Entregas

| Item | Detalhe |
|------|---------|
| Pagina | `desktop/equipment.py` |
| Equipamento | CRUD tipo/nome/backend/disponivel |
| Setup | camera + mount + focuser → `instrument_configs` |
| Programa | combo Setup no dialog; botao Atribuir a programa |

## Fluxo

1. Equipamento → Novo (camera/mount/focuser, backend sim)
2. Novo setup → escolher papeis
3. Atribuir a programa (ou editar Programa → Setup instrumental)
4. Sessao wizard usa `default_instrument_config_id` no bloco

## Sequencia seguinte (ENTRADA #4)

Editor visual log + formulario solar (PO-F03 / PO-E03 GUI).
