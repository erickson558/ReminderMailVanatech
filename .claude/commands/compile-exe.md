---
description: Compila el proyecto a un ejecutable .exe usando PyInstaller. Verifica dependencias, limpia builds anteriores y genera el .exe con el ícono. Uso: /compile-exe
---

Vas a compilar ReminderMailVanatech a un ejecutable Windows (.exe) usando PyInstaller.

**Directorio del proyecto:** `d:\OneDrive\Regional\1 pendientes para analisis\proyectospython\ReminderMailBrianvanatech`

## Pasos

### 1. Verificar dependencias
```powershell
python --version
pip show pyinstaller
pip show pywin32
```
Si falta pyinstaller o pywin32, instalarlos:
```powershell
pip install -r "d:\OneDrive\Regional\1 pendientes para analisis\proyectospython\ReminderMailBrianvanatech\requirements.txt"
```

### 2. Verificar que main.py existe y es el punto de entrada correcto
Leer `main.py` para confirmar que importa `from frontend.app import run_app`.

### 3. Verificar que el spec está actualizado
Leer `reminderfactura.spec` y confirmar:
- Entry point es `main.py`
- `datas` incluye `('i18n', 'i18n')`
- `icon` apunta a `reminderagua.ico`
- `console=False` (sin ventana de consola)

### 4. Limpiar builds anteriores
```powershell
Remove-Item -Recurse -Force "d:\OneDrive\Regional\1 pendientes para analisis\proyectospython\ReminderMailBrianvanatech\build" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "d:\OneDrive\Regional\1 pendientes para analisis\proyectospython\ReminderMailBrianvanatech\dist" -ErrorAction SilentlyContinue
```

### 5. Compilar
```powershell
cd "d:\OneDrive\Regional\1 pendientes para analisis\proyectospython\ReminderMailBrianvanatech"
pyinstaller reminderfactura.spec
```

### 6. Verificar resultado
```powershell
Test-Path "d:\OneDrive\Regional\1 pendientes para analisis\proyectospython\ReminderMailBrianvanatech\dist\reminderfacturavanatech.exe"
Get-Item "d:\...\dist\reminderfacturavanatech.exe" | Select-Object Name, Length, LastWriteTime
```

### 7. Reportar al usuario
- Resultado de la compilación (éxito o errores)
- Tamaño y ubicación del .exe generado
- Instrucciones de distribución:
  - El archivo `dist/reminderfacturavanatech.exe` es autocontenido.
  - Al ejecutarlo por primera vez creará `config.json` en la misma carpeta.
  - `reminder_mail.log` también se crea junto al .exe.
  - NO requiere Python instalado en el equipo destino.
  - SÍ requiere Microsoft Outlook (si se usa el método Outlook COM).

## Posibles errores comunes

- **`win32com` not found**: Asegurarse que pywin32 está instalado con `pip install pywin32`.
- **`UPX not found`**: Ignorar o desactivar UPX en el spec con `upx=False`.
- **Antivirus bloquea**: Los ejecutables PyInstaller a veces son detectados como falsos positivos; agregar excepción al antivirus.
