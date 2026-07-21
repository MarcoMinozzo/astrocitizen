# Smoke do binario Windows (AC-076)
param(
  [string]$Bin = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
if (-not $Bin) {
  $Bin = Join-Path $Root "dist\astrocitizen.exe"
}
if (-not (Test-Path $Bin)) {
  throw "Binario nao encontrado: $Bin"
}

$Tmp = Join-Path $env:TEMP ("astrocitizen-smoke-" + [guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $Tmp | Out-Null
$Db = Join-Path $Tmp "smoke.sqlite3"
$Art = Join-Path $Tmp "artifacts"

& $Bin version
& $Bin modules
& $Bin init-db --db $Db --artifacts $Art
& $Bin site add --db $Db --name Smoke --lat -29.7 --lon -51.1 --default
& $Bin site list --db $Db
& $Bin meteo forecast --db $Db --date 2026-07-21 --provider manual

Write-Host "SMOKE_OK bin=$Bin"
