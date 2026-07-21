# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

datas = []
datas += collect_data_files('astrocitizen')


a = Analysis(
    ['../src/astrocitizen/__main__.py'],
    pathex=['src'],
    binaries=[],
    datas=datas,
    hiddenimports=['astrocitizen.cli', 'astrocitizen.adapters.sky.astropy_ephemeris', 'astrocitizen.adapters.meteo.open_meteo', 'astrocitizen.adapters.meteo.manual', 'astrocitizen.adapters.hardware'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5', 'PyQt6', 'PySide6', 'PySide2'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='astrocitizen',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
