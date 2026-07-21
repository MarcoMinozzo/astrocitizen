#!/usr/bin/env bash
# Build AstroCitizen com PyInstaller (AC-075).
# Linux: dist/astrocitizen ù Windows: dist/astrocitizen.exe
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python3 -m pip install -U pip
python3 -m pip install -e ".[dev,packaging]"

python3 -m PyInstaller \
  --name astrocitizen \
  --onefile \
  --noconfirm \
  --console \
  --paths src \
  --collect-data astrocitizen \
  --hidden-import astrocitizen.cli \
  --hidden-import astrocitizen.adapters.sky.astropy_ephemeris \
  --hidden-import astrocitizen.adapters.meteo.open_meteo \
  --hidden-import astrocitizen.adapters.meteo.manual \
  --hidden-import astrocitizen.adapters.hardware \
  --exclude-module PyQt5 \
  --exclude-module PyQt6 \
  --exclude-module PySide6 \
  --exclude-module PySide2 \
  --distpath dist \
  --workpath build \
  --specpath packaging \
  src/astrocitizen/__main__.py

echo "Artefacto: dist/astrocitizen (Linux) ou dist/astrocitizen.exe (Windows)"
echo "Smoke: dist/astrocitizen version && dist/astrocitizen modules"
echo "GUI: instalar PySide6 e rebuild sem --exclude-module PySide6 (ver packaging/README.md)"
