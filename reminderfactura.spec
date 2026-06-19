# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec para ReminderMailVanatech
#
# Compilar con:
#   pyinstaller reminderfactura.spec
#
# El ejecutable generado se encontrará en dist/reminderfacturavanatech.exe
# No requiere consola (windowed=True) y usa el ícono reminderagua.ico.
#
# Notas importantes:
#   - Los archivos i18n/ se empaquetan dentro del .exe y se extraen en tiempo
#     de ejecución a sys._MEIPASS (directorio temporal).
#   - config.json NO se empaqueta: se crea/lee/escribe junto al ejecutable
#     para que la configuración persista entre ejecuciones.

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # Incluir carpeta de traducciones dentro del ejecutable
        ('i18n', 'i18n'),
        # Incluir el ícono (aunque también se referencia en EXE, algunos entornos
        # lo necesitan disponible como dato)
        ('reminderagua.ico', '.'),
    ],
    hiddenimports=[
        # Módulos win32com cargados dinámicamente que PyInstaller no detecta
        'win32com.client',
        'win32api',
        'win32con',
        'pywintypes',
        'win32com.gen_py',
        # Módulos internos del proyecto
        'backend',
        'backend.logger_setup',
        'backend.config_manager',
        'backend.email_service',
        'frontend',
        'frontend.app',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='reminderfacturavanatech',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,           # Sin ventana de consola (app de escritorio)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='reminderagua.ico', # Ícono de la aplicación
)
