# Contribuir para o AstroCitizen

Obrigado pelo interesse. Este repositório está a sair da **Fase 0 (especificação)** para a **Fase 1 (implementação)**.

## Antes de codificar

1. Ler [docs/INDEX.md](docs/INDEX.md) e o [PRODUCT_BACKLOG.md](docs/PRODUCT_BACKLOG.md).  
2. Respeitar **D-010** (otimização de recursos) e a arquitectura hexagonal ([ARQUITETURA.md](docs/ARQUITETURA.md)).  
3. Domínio e ports **não** importam UI, Alpyca, SQL ou Astroquery directamente.  
4. Desktop = **PySide6** (D-009.4-rev); SaaS = FastAPI + Next.js + BDaaS (D-009).  
5. DoD Windows: caminho para `.exe` (AC-075) não pode ser quebrado por decisões de stack.

## Ambiente local

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows
# .venv\Scripts\activate

pip install -U pip
pip install -e ".[dev]"
pytest -q
ruff check src tests
astrocitizen version
astrocitizen modules
```

Requisitos: **Python ≥ 3.10**.

## Estrutura do código (S0)

```text
src/astrocitizen/
  shared/          # erros, IDs
  ports/           # interfaces hexagonais
  application/     # casos de uso (vazio → S1+)
  workspace|planning|inventory|programs|observatory|
  reduction|archive|contribution|sync/
  adapters/        # implementações (S1+)
  cli.py
```

Schema alvo: [docs/MODELO_DADOS_V1.md](docs/MODELO_DADOS_V1.md).

## Pull requests

- Uma preocupação por PR quando possível.  
- Testes a passar no CI (Linux + Windows).  
- Mensagens de commit focadas no *porquê*.  
- Não commitar secrets (`.env`, credenciais de redes).

## Sprint actual

**S0** — skeleton + CI (AC-001…004).  
Seguinte: **S1** — persistência + Site/Equipamento/Programas (AC-010…024).

## Contacto / produto

Issues e PRs no GitHub do repositório. Decisões de produto em `docs/decisoes/`.
