# Sprint — i18n + Ajuda in-app (RN-120 / RN-121)

**Data:** 2026-07-22  
**Estado:** concluido  
**Regras:** [ESCOPO_GERAL_E_REGRAS_DE_NEGOCIO.md](ESCOPO_GERAL_E_REGRAS_DE_NEGOCIO.md) RN-120, RN-121

Nota: os IDs RN-110/111 do estudo inicial colidem com persistencia; as regras UX usam **RN-120** (idioma) e **RN-121** (ajuda).

## Entregas

1. `shared/i18n.py` — deteccao SO, preferencia, fallback `en`, `t(key)`.
2. Catalogos `shared/locales/{en,pt,es}.json`.
3. Prefs QSettings `ui_lang_pref` (`auto` default).
4. Desktop: botao Ajuda + F1; Configurar → Preferencias + Ajuda.
5. Chrome da shell (nav, brand, ContextBar labels) traduzido.

## Resolucao de lingua

`preferencia` ∈ {auto, pt, es, en} → se auto, mapear locale SO (`pt_BR`→`pt`, …) → se nao suportado → `en`.

## Fora desta sprint

- Traduzir todos os paineis tecnicos e CLI.
- SaaS `Accept-Language` (reutiliza o mesmo resolver).
- Assistente RAG (E19).
