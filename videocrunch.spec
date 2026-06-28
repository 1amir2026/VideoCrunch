# -*- mode: python ; coding: utf-8 -*-
# VideoСrunch — PyInstaller build spec

import sys
from pathlib import Path

block_cipher = None

# Bundled FFmpeg binaries (placed in ./bin/ before running pyinstaller)
bin_dir = Path("bin")
suffix  = ".exe" if sys.platform == "win32" else ""

binaries = []
ffmpeg_path  = bin_dir / f"ffmpeg{suffix}"
ffprobe_path = bin_dir / f"ffprobe{suffix}"

if ffmpeg_path.exists():
    binaries.append((str(ffmpeg_path), "."))
if ffprobe_path.exists():
    binaries.append((str(ffprobe_path), "."))

a = Analysis(
    ["videocrunch.py"],
    pathex=[],
    binaries=binaries,
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="videocrunch",
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
    icon=None,
)
