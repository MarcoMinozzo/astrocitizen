# Sprint — Radio AC-161 (PO-I02..I04)

**Data:** 2026-07-23  
**Estado:** concluido  
**Base:** [SPRINT_RADIO_ENTRADA6.md](SPRINT_RADIO_ENTRADA6.md), AC-160

## Entregas

| Componente | Papel |
|------------|--------|
| `parse_radio_spectrum_csv` | `freq_mhz,power` → pontos x=MHz |
| `parse_radio_scan_csv` | `t_utc,power[,az/el/ha]` → `radio_scan` |
| `ImportRadioSpectrum` / `ImportRadioScan` | Persistencia + lab_notes |
| CLI | `import radio --kind series\|spectrum\|scan [--lab-notes]` |
| GUI Radio | Modo Serie / Espectro / Drift + lab notes |
| Workflows | PO-I02, PO-I03, PO-I04 |

## Uso

```bash
astrocitizen import radio --path sun.csv --freq 1420.4
astrocitizen import radio --kind spectrum --path hi.csv
astrocitizen import radio --kind scan --path drift.csv
astrocitizen import radio --kind series --path vhf.csv --lab-notes "Yagi 2m"
```

## Fora deste slice

- Waterfall 2D / WAV
- Fit da linha HI / calibracao RF
- Export rede clubes-radio

## DoD

- [x] Parsers + imports I02/I03
- [x] lab_notes (I04 thin)
- [x] CLI --kind + GUI modos
- [x] Workflows + guide steps
- [x] Testes `test_radio_ac161.py`
- [x] ENTRADA / backlog AC-161
