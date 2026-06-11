# PyInstaller spec — génère un exécutable autonome (aucun Python requis)
# Build: pyinstaller petrix_agent.spec

block_cipher = None

a = Analysis(
    ['petrix_agent/cli.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'petrix_agent.scanner.network',
        'petrix_agent.scanner.ports',
        'petrix_agent.reporter',
        'netifaces',
        'nmap',
        'httpx',
        'click',
        'rich',
        'rich.console',
        'rich.progress',
        'rich.table',
    ],
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
    name='petrix-agent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
