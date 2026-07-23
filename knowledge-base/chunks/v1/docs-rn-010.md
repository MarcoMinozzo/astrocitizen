---
chunk_id: docs-rn-010
source_id: docs-rn
path: docs/ESCOPO_GERAL_E_REGRAS_DE_NEGOCIO.md
title: 9. Fontes de dados (negócio → tecnologia)
trust_tier: T3
lang: pt
topics: ["rules", "product"]
po_id: null
network: iota
pipeline_stage: help
token_estimate: 392
chunk_hash: "sha256:83d1769a6bde8705bcad546196d8b475ad40c5c26d52c35dd90dcb80dbbde2b1"
corpus_version: 0.1.0-kb1
---

## 9. Fontes de dados (negócio → tecnologia)

| Necessidade de negócio | Fonte típica |
|------------------------|--------------|
| Coordenadas / tempo / AltAz | Astropy |
| NEOs / órbitas / Horizons | Astroquery |
| Nomes de alvos | SIMBAD / catálogos |
| Meteo do site | API meteo +/ou ASCOM ObservingConditions + entrada manual |
| Controle instrumental | Alpyca / udrv SBIG / simulador |
| Previsões de ocultação | Import IOTA / arquivos de previsão |

Detalhe técnico: `STACK_TECNOLOGICA.md`.

---

## 10. Critérios de aceite de negócio (Fase de produto)

A especificação de negócio está atendida quando o sistema permitir, de ponta a ponta:

1. Cadastrar Site e equipamento.  
2. Ativar pelo menos dois ProgramasObservacionais distintos.  
3. Gerar ProgramaDiario com efemérides + meteo + validação de equipamento.  
4. Executar ou importar Observacoes e analisá-las conforme o tipo.  
5. Atualizar o estado dos programas e preparar export para rede.  

A cobertura de **todos** os tipos científicos permanece em `ESCOPO_CITIZEN_SCIENCE.md`; este documento garante o **esqueleto operacional** comum a todos eles.

---

## 11. Próximos artefatos derivados

| Artefato | Conteúdo |
|----------|----------|
| [WORKFLOWS.md](WORKFLOWS.md) | Fluxos UI passo a passo (planejar noite, executar, analisar) |
| `API_ALVO.md` | Contratos dos serviços de domínio e API SaaS ↔ Desktop |
| Atualização `BACKLOG.md` | Épicos BN-* mapeados às RN |

---

## 12. Glossário rápido

| Termo | Significado |
|-------|-------------|
| Efeméride observacional | Posição/circunstância do alvo **como vista do Site** no tempo T |
| Programa observacional | Campanha científica contínua |
| Programa diário | Plano da noite/dia para um Site |
| Configuração instrumental | Conjunto de equipamentos da observação |
| Citizen science | Produção de dados astronômicos úteis a redes/ciência por não-profissionais ou pequenos observatórios |
