# Empacote Desktop ? PyInstaller (AC-075 / AC-076)

**Objectivo:** `.exe` Windows utilizavel sem Python no PATH do utilizador final (DoD Desktop).

Espelha o padrao do `sbig-suite`: **onefile** + smoke CLI em CI.

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

O build CI **exclui** PySide6 para manter o binario CLI mais leve e o smoke estavel.
Para um `.exe` com `astrocitizen gui`:

1. `pip install PySide6`
2. Remover `--exclude-module PySide6` do comando / script
3. Opcional: `--hidden-import astrocitizen.desktop.app`

Drivers de hardware (SBIG udrv / ASCOM Alpaca) **nao** vao dentro do `.exe` ?
instalacao de sistema separada.

## Browser AAVSO (Qt WebEngine, AC-095)

O `.exe` / build base **nao** inclui Chromium (D-010). Por defeito o painel
**Observatorio → Campanhas AAVSO** usa o **browser do sistema** (mais estavel;
evita segfaults Chromium em alguns Linux/GPU).

Browser embutido (opt-in):

```bash
pip install 'astrocitizen[gui-web]'   # PySide6-WebEngine
export ASTROCITIZEN_WEBENGINE=1
astrocitizen gui
```

Um instalador "full" com WebEngine exigiria `--collect-all PySide6` /
plugins `QtWebEngineProcess` e aumenta ~80–150 MB.

## onedir vs onefile

- **onefile** (default CI): um ficheiro; arranque um pouco mais lento.
- **onedir**: pasta com DLL; arranque mais rapido (bom para GUI). Trocar `--onefile` por `--onedir`.

## CI

Job `windows-exe` em `.github/workflows/ci.yml` ? build + smoke + upload do artefacto `astrocitizen-windows`.
