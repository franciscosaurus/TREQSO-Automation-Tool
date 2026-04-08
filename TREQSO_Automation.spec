# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for TREQSO Automation Tool v2.1

What this bundles (inside the .exe):
  - Python runtime
  - treqso_gui.py + treqso_processor.py
  - All Python dependencies (python-dotenv, pywin32, tkinter)
  - Sample CSV files and Excel templates (embedded so the GUI can read them)
  - .env.template (default config reference)

What is NOT bundled (placed separately by the Inno Setup installer):
  - node_portable/node.exe  → {app}/node_portable/node.exe
  - dist/cli.js + dist/treqso-automation.js  → {app}/dist/
  - node_modules/  → {app}/node_modules/
  - .env  → {app}/.env

At runtime, treqso_processor._get_app_dir() resolves to dirname(sys.executable),
which is the install root where all the above live.
"""

import os

block_cipher = None

# Files to embed inside the executable
# These are resources the Python/GUI layer reads directly (not subprocess calls).
added_files = []

required_files = [
    ('sample_parts.csv', '.'),
    ('sample_bom.csv',   '.'),
    ('sample_edit_parts.csv',   '.')
]

optional_files = [
    ('Parts_Template.csv', '.'),
    ('BOMs_Template.csv',  '.'),
    ('Edit_Parts_Template.csv',  '.'),
    ('.env.template',       '.'),
    # package.json is NOT embedded — node reads it from the install dir on disk.
    # dist/*.js are NOT embedded — node reads them from {app}/dist/ on disk.
    # node_portable/node.exe is NOT embedded — it lives next to the .exe on disk.
]

for src, dest in required_files:
    if os.path.exists(src):
        added_files.append((src, dest))
    else:
        print(f"WARNING: Required file missing: {src}")

for src, dest in optional_files:
    if os.path.exists(src.replace('*', '')) or ('*' in src and os.path.exists(os.path.dirname(src))):
        added_files.append((src, dest))
    else:
        print(f"INFO: Optional file not found (skipping): {src}")

# Hidden imports PyInstaller might not detect automatically
hidden_imports = [
    'dotenv',
    'win32print',
    'win32api',
    'win32con',
    'pywintypes',
]

a = Analysis(
    ['treqso_gui.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Keep the bundle lean — none of these are used
        'matplotlib', 'numpy', 'pandas', 'scipy',
        'PIL', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6',
    ],
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
    name='TREQSO_Automation',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,   # GUI only — no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)
