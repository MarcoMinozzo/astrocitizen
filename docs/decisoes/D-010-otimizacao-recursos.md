# D-010 — Otimização técnica e uso eficiente de recursos

**Data:** 2026-07-21  
**Status:** aceito (princípio transversal)

## Decisão

Todas as soluções propostas e implementadas no AstroCitizen devem ser pautadas na **melhor otimização técnica** e no **melhor uso de recursos computacionais**, sem sacrificar corretude científica nem os DoD de produto (ex.: `.exe` Windows utilizável).

## Critérios de avaliação (obrigatórios em ADRs e designs)

Ao comparar alternativas, documentar explicitamente:

| Critério | Perguntas |
|----------|-----------|
| **CPU** | Trabalho em idle? Trabalho por frame/exposição? Evita polling desnecessário? |
| **RAM** | Quantos processos/runtimes? Footprint em sessão noturna longa? |
| **I/O e rede** | Sync em batch vs chatty? Uploads retomáveis? Cache local? |
| **Latência crítica** | Controlo de hardware e abort de exposição sem hops inúteis (IPC, cloud)? |
| **Complexidade operacional** | Menos moving parts = menos falhas e menos custo de manutenção |
| **Empacote / CI** | Custo de build e tamanho do artefacto justificados? |

## Regras práticas

1. **Preferir um runtime** quando o domínio já vive nele (ex.: Desktop Python+PySide, não sidecar sem necessidade).  
2. **Não colocar na cloud** o que exige baixa latência ou offline (hardware, sessão).  
3. **Não colocar no Desktop** o que escala melhor como BDaaS (arquivo mestre, análise pesada batch).  
4. **Persistência:** metadados em BD; blobs em object store; evitar duplicar FITS sem necessidade.  
5. **Idle barato:** observatório em espera não deve consumir como uma sessão activa.  
6. **Medir antes de otimizar micro,** mas **escolher arquitectura** já com custo em mente (decisões A/B com tabela de recursos).  
7. Alinhamento a outro produto (ex.: motorsport) **não prevalece** sobre este princípio se aumentar custo sem ganho claro.

## Checklist rápido (usar em novas propostas)

- [ ] Quantos processos/runtimes em runtime?
- [ ] Qual o custo em idle vs sessão activa?
- [ ] O caminho crítico (hardware / abort) tem hops desnecessários?
- [ ] Há BD/serviço extra que JSONB ou object store já cobrem?
- [ ] A alternativa mais “bonita” ou “igual ao outro repo” é também a mais eficiente?
- [ ] O DoD (ex. `.exe` Windows) fica cumprido sem inflacionar recursos sem necessidade?

## Exemplos já aplicados

| Decisão | Otimização |
|---------|------------|
| D-009.4-rev PySide6 vs Tauri+sidecar | Menos processos, menos RAM, latência directa ao hardware |
| BDaaS + object store | VM de app sem estado pesado; storage gerido |
| JSONB no Postgres (MVP) vs Mongo extra | Evita segundo motor de BD |
| Sync offline-first | Sessão sem depender de rede contínua |

## Consequências

- Novos ADRs e docs de arquitectura devem incluir secção **“Custo de recursos”**.  
- Revisões de stack usam este documento como critério de desempate.  
- Trade-offs conscientes (ex.: `.exe` maior por incluir Qt) são aceites se forem o menor custo *global* para o DoD.
