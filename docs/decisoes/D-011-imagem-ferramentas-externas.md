# D-011 — Tratamento de imagem: ferramentas externas, nao suite interna

**Data:** 2026-07-23  
**Estado:** aceite  
**Contexto:** equipa nao e especialista em processamento estetico/avancado de imagens astronomicas; produto e citizen-science + reporte a redes.

## Decisao

1. **Nao** construir um Siril/PixInsight/IRAF dentro do AstroCitizen.
2. AstroCitizen e dono do **registo** (Observation, Artifact, AnalysisProduct, NetworkSubmission).
3. Processamento pesado de imagem fica em **ferramentas open-source externas** (Siril, SAOImageDS9, ASTAP, …) lancadas via **`ImageToolPort`**.
4. Medidas cientificas ja no produto (fotometria, espectro, plate-solve, calib basica, viewer stretch) **permanecem** embutidas — sao dominio CS, nao “tratamento estetico”.
5. Prioridade de produto imediata: **reporte as redes** (AC-141 + UI Revisar) sobre expansao E19 ou imaging suite.

## Integracao

```text
Artifact FITS no store
  -> Abrir em ferramenta externa (comando configuravel)
  -> utilizador processa
  -> reimporta resultado (Importar) -> novo Artifact / produto
```

Prefs: comando por ferramenta (`siril %f`, `ds9 %f`). Fallback: abrir com o SO (`QDesktopServices`).

## Fora de ambito (por agora)

- Lucky imaging / stack planetario completo (AC-130) como motor interno
- Clone de formularios web das instituicoes (so contrato de dados + checklist)
- Dependencia SaaS para processar FITS

## Relacionados

- Atlas: [ATLAS_REPORTE_OBSERVACOES.md](../atlas/ATLAS_REPORTE_OBSERVACOES.md)
- Prioridade redes: AC-141…  
- Imaging externo: AC-134 (ImageToolPort)
