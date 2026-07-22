# Sprint — Interpretacao espectral (AC-106)

Assistencia estilo ARAS/citizen: catalogo de linhas, telurico, pista de classe grosseira, e comparacao multi-epoca (ex.: SN2026sqf).

## Entregas

| Item | Detalhe |
|------|---------|
| Modulo | `analysis/spectrum_report.py` · `InterpretSpectrum` |
| Produto | `spectrum_report` + `.txt` `#TYPE=ASTROCITIZEN_SPECTRUM_REPORT` |
| CLI | `astrocitizen analyze spectrum-report --fits-uri ...` |
| Multi-epoca | `--extra-products uuid1,uuid2` |
| Workflows | `interpret_spectrum` em PO-B01 / B02 / B03 |

## Uso

```bash
# Apos extract 1D (ou FITS BeSS/ARAS)
astrocitizen analyze spectrum-report --fits-uri file:///.../spectrum.fits --out /tmp/report.txt

# Comparar epocas (produtos spectrum_1d)
astrocitizen analyze spectrum-report --product <uuid> --extra-products <uuid2>,<uuid3>
```

## Limites (explicitos)

- Assistivo: nao substitui templates SN / classificacao humana.
- Catalogo fixo (Balmer, He, Si II, Na D, O2 telurico, Ca II).
- EW / gauss fit / redshift preciso ficam para AC-102 completo.

## Checklist

- [x] Detect lines + class hint + epochs
- [x] CLI + produto no BD
- [x] Workflows PO-B*
- [x] Testes
- [x] Backlog AC-106
- [ ] Painel GUI Analisar (proxima onda)
