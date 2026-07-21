#!/usr/bin/env bash
# Smoke do binario empacotado (AC-076).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN="${1:-}"
if [[ -z "$BIN" ]]; then
  if [[ -x "$ROOT/dist/astrocitizen.exe" ]]; then
    BIN="$ROOT/dist/astrocitizen.exe"
  elif [[ -x "$ROOT/dist/astrocitizen" ]]; then
    BIN="$ROOT/dist/astrocitizen"
  else
    echo "Uso: $0 path/to/astrocitizen[.exe]" >&2
    exit 2
  fi
fi

TMP="${TMPDIR:-/tmp}/astrocitizen-smoke-$$"
mkdir -p "$TMP"
DB="$TMP/smoke.sqlite3"
ART="$TMP/artifacts"

"$BIN" version
"$BIN" modules
"$BIN" init-db --db "$DB" --artifacts "$ART"
"$BIN" site add --db "$DB" --name Smoke --lat -29.7 --lon -51.1 --default
"$BIN" site list --db "$DB"
"$BIN" meteo forecast --db "$DB" --date 2026-07-21 --provider manual -v | head -5 || true

echo "SMOKE_OK bin=$BIN"
