# Setup Omni Simulator / backends (AC-047)

**Estado:** notas S3 — hardware real via Alpaca fica para ambiente com Omni Simulator.

## Backends

| Backend | Uso | Estado no AstroCitizen |
|---------|-----|------------------------|
| `sim` | Desenvolvimento e CI | Completo (Camera/Mount/Focuser) |
| `alpaca` | ASCOM Alpaca + Alpyca | Stub — requer `pip install '.[alpaca]'` + Omni |
| `udrv` | SBIG Universal Driver | Stub — integração no repo `sbig-suite` (AC-042) |

```bash
# Factory
from astrocitizen.adapters.hardware import create_camera, create_mount, create_focuser
cam = create_camera("sim")
cam.connect()
cam.expose(exptime_s=1.0)
```

## Omni Simulator (Windows / Linux)

1. Instalar [ASCOM Alpaca Omni Simulators](https://github.com/ASCOMInitiative/ASCOM.Alpaca.Simulators).
2. Arrancar Camera / Telescope / Focuser no porto (default `11111`).
3. `pip install 'astrocitizen[alpaca]'` e apontar host/port nos stubs (ligação completa em sprint seguinte).

## CLI de sessão (simulador)

```bash
astrocitizen session start --plan <plan-uuid>
astrocitizen session capture --session <id> --block <block-uuid> --exptime 1
astrocitizen session end --session <id>
```
