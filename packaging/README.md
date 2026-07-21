# Empacote Desktop ù PyInstaller (AC-075 / AC-076)

**Objectivo:** `.exe` Windows utilizùvel sem Python no PATH do utilizador final (DoD Desktop).

Espelha o padrùo do `sbig-suite`: **onefile** + smoke CLI em CI.

## Build local

```bash
# Linux / macOS / Git Bash
chmod +x scripts/build_pyinstaller.sh scripts/smoke_exe.sh
./scripts/build_pyinstaller.sh
./scripts/smoke_exe.sh
```

Windows (PowerShell):

```powershell
pip install -e ".[dev,packaging]"
pyinstaller --name astrocitizen --onefile --noconfirm --console --paths src `
  --collect-data astrocitizen `
  --hidden-import astrocitizen.cli `
  --exclude-module PyQt5 --exclude-module PyQt6 `
  --exclude-module PySide6 --exclude-module PySide2 `
  --distpath dist --workpath build --specpath packaging `
  src/astrocitizen/__main__.py
.\scripts\smoke_exe.ps1
```

Artefacto: `dist/astrocitizen.exe` (Windows) ou `dist/astrocitizen` (Linux).

## Smoke

O script confirma:

1. `version` / `modules`
2. `init-db` + `site add/list` (SQLite + templates PO-*)
3. `meteo forecast --provider manual` (sem rede)

## GUI (PySide6)

O build CI **exclui** PySide6 para manter o binùrio CLI mais leve e o smoke estùvel.
Para um `.exe` com `astrocitizen gui`:

1. `pip install PySide6`
2. Remover `--exclude-module PySide6` do comando / script
3. Opcional: `--hidden-import astrocitizen.desktop.app`

Drivers de hardware (SBIG udrv / ASCOM Alpaca) **nùo** vùo dentro do `.exe` ù instalaùùo de sistema separada.

## onedir vs onefile

- **onefile** (default CI): um ficheiro; arranque um pouco mais lento.
- **onedir**: pasta com DLL; arranque mais rùpido (bom para GUI). Trocar `--onefile` por `--onedir`.

## CI

Job `windows-exe` em `.github/workflows/ci.yml` ù build + smoke + upload do artefacto `astrocitizen-windows`.
