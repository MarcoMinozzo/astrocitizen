# Sprint — Wizard Sessao (IN-CAP)

Captura GUI: site + programa + alvo → plano da noite → sessao → FITS (sim/alpaca/udrv).

## Entregas

| Item | Detalhe |
|------|---------|
| Helper | `observatory/quick_session.py` · `prepare_wizard_session` |
| Archive | `add_observation_block` |
| Capture | `program_id` / `target_id` opcionais sem bloco |
| GUI | `desktop/session_panel.py` na nav **Sessao** |

## Uso GUI

1. Cadastre Site / Programa / Alvo (CRUD).
2. **Sessao** → selecionar → **Iniciar sessao**.
3. Backend `sim`, exposicao, N frames → **Capturar**.
4. Log mostra `obs=` e caminho FITS; **Terminar sessao**.

## Checklist

- [x] Prepare plano+bloco+sessao
- [x] Multi-frame com reset de bloco
- [x] Painel GUI
- [x] Testes
