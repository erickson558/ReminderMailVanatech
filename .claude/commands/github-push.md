---
description: Sube los cambios al repositorio GitHub de erickson558. Inicializa el repo si no existe, crea .gitignore, hace commit y push. Uso: /github-push "mensaje del commit"
---

Vas a subir los cambios del proyecto ReminderMailVanatech a GitHub con la cuenta erickson558.

**Directorio del proyecto:** `d:\OneDrive\Regional\1 pendientes para analisis\proyectospython\ReminderMailBrianvanatech`

## Pasos a seguir

### 1. Verificar estado actual
```powershell
git -C "d:\OneDrive\Regional\1 pendientes para analisis\proyectospython\ReminderMailBrianvanatech" status
git -C "d:\OneDrive\Regional\1 pendientes para analisis\proyectospython\ReminderMailBrianvanatech" log --oneline -5
```

### 2. Crear .gitignore si no existe
Si no existe `.gitignore`, créalo con este contenido:
```
build/
dist/
__pycache__/
*.pyc
*.pyo
*.log
.vscode/
.idea/
Thumbs.db
venv/
env/
*.exe
```
**IMPORTANTE:** No ignorar `config.json` a menos que contenga contraseñas SMTP reales en el campo `password`. Si `password` está vacío o en blanco, incluir `config.json` en el commit.

### 3. Verificar que config.json no tenga credenciales sensibles
Leer `config.json` y verificar que `smtp_config.password` esté vacío. Si tiene contraseña, advertir al usuario antes de incluirlo.

### 4. Inicializar repo local si no existe
```powershell
if (-not (Test-Path "d:\OneDrive\Regional\1 pendientes para analisis\proyectospython\ReminderMailBrianvanatech\.git")) {
    git -C "d:\OneDrive\Regional\1 pendientes para analisis\proyectospython\ReminderMailBrianvanatech" init
    git -C "d:\OneDrive\Regional\1 pendientes para analisis\proyectospython\ReminderMailBrianvanatech" branch -M main
}
```

### 5. Crear repositorio en GitHub si no existe
```powershell
gh repo view erickson558/ReminderMailVanatech 2>$null
# Si no existe, crearlo:
gh repo create erickson558/ReminderMailVanatech --public --description "Aplicación de recordatorio de facturas vía correo electrónico"
```

### 6. Configurar remote si no está configurado
```powershell
git -C "..." remote get-url origin 2>$null || git -C "..." remote add origin https://github.com/erickson558/ReminderMailVanatech.git
```

### 7. Agregar archivos y hacer commit
Usa el mensaje de commit proporcionado como argumento `$ARGUMENTS`, o usa un mensaje descriptivo por defecto.

```powershell
git -C "d:\OneDrive\Regional\1 pendientes para analisis\proyectospython\ReminderMailBrianvanatech" add .gitignore
git -C "..." add backend/ frontend/ i18n/ main.py requirements.txt config.json reminderfactura.spec CLAUDE.md SDD.md .claude/
git -C "..." commit -m "$ARGUMENTS

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

### 8. Push
```powershell
git -C "..." push -u origin main
```

### 9. Mostrar URL del repositorio
```powershell
gh repo view erickson558/ReminderMailVanatech --web  # opcional: abrir en browser
Write-Output "Repositorio: https://github.com/erickson558/ReminderMailVanatech"
```

Reporta al usuario:
- Si el push fue exitoso o si hubo errores.
- La URL del repositorio en GitHub.
- Cuántos archivos se subieron.
