# LeftOverSaver.spec for PyInstaller
# Usage: pyinstaller LeftOverSaver.spec

block_cipher = None

import sys
from pathlib import Path

# Main script path
script_path = 'LeftOverSaver.py'

# Data files to include (relative to project root)
datas = [
    (str(Path('data') / 'api_key.txt'), 'data'),
    (str(Path('data') / 'ingredients_data.json'), 'data'),
    (str(Path('data') / 'settings.json'), 'data'),
]
print (datas)

# Hidden imports (if needed)
hiddenimports = []

from PyInstaller.utils.hooks import collect_submodules
hiddenimports += collect_submodules('openai')

# Build the executable
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

a = Analysis(
    [script_path],
    pathex=[str(Path().resolve())],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LeftOverSaver',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)