# ReminderMailVanatech — Guía para Claude Code

## ¿Qué es este proyecto?

Aplicación de escritorio Windows que envía correos de recordatorio de factura de forma automática.
Se ejecuta, envía el correo 1 segundo después de abrirse, y se cierra automáticamente.

**Cuenta GitHub:** erickson558
**Repositorio:** https://github.com/erickson558/ReminderMailVanatech

## Stack tecnológico

- **Python 3** con Tkinter (GUI)
- **win32com** (Outlook COM) para envío via Outlook de escritorio
- **smtplib + STARTTLS** para envío via Hotmail/Gmail sin Outlook
- **PyInstaller** para compilar a .exe
- **i18n** con JSON (español/inglés)

## Estructura del proyecto

```
main.py                    ← Punto de entrada (solo bootstrapping)
backend/
  logger_setup.py          ← Logging a archivo reminder_mail.log
  config_manager.py        ← Carga/guardado de config.json
  email_service.py         ← Envío Outlook COM o SMTP
frontend/
  app.py                   ← GUI con ReminderMailApp (Tkinter)
i18n/
  es.json                  ← Textos en español
  en.json                  ← Textos en inglés
config.json                ← Configuración persistente (destinatarios, asunto, etc.)
reminderfactura.spec       ← Spec PyInstaller para generar .exe
reminderagua.ico           ← Ícono del ejecutable
requirements.txt           ← Dependencias Python
SDD.md                     ← Especificaciones del sistema
.claude/
  agents/                  ← Agentes especializados
  commands/                ← Skills (slash commands)
```

## Cómo ejecutar

```powershell
# En el directorio del proyecto:
python main.py
```

## Cómo compilar a .exe

```powershell
pip install -r requirements.txt
pyinstaller reminderfactura.spec
# El .exe queda en dist/reminderfacturavanatech.exe
```

## Métodos de envío de correo

### Outlook COM (método por defecto)
- Requiere Microsoft Outlook instalado y configurado.
- La cuenta debe estar agregada en Outlook → Archivo → Configuración de cuenta.
- NO necesita contraseña en config.json.

### SMTP / Hotmail (alternativa)
- Funciona sin Outlook instalado.
- Configurar en la GUI: seleccionar "SMTP (Hotmail/Gmail)".
- Servidor Hotmail: `smtp-mail.outlook.com`, puerto `587`.
- Si la cuenta tiene 2FA, usar "Contraseña de aplicación" (App Password).
- Gmail: `smtp.gmail.com`, puerto `587`, requiere App Password.

## Skills disponibles (slash commands)

| Comando | Descripción |
|---|---|
| `/github-push` | Commit y push a GitHub con cuenta erickson558 |
| `/comment-code` | Documenta el código con comentarios explicativos |
| `/improve-code` | Refactorización como ingeniero senior |
| `/compile-exe` | Compila el proyecto a .exe con PyInstaller |
| `/update-sdd` | Sincroniza SDD.md con el estado actual del código |

## Agentes disponibles

| Agente | Descripción |
|---|---|
| `github-agent` | Especializado en GitHub y git |
| `python-senior` | Arquitectura y refactorización Python |
| `code-commenter` | Documentación de código |

## Comportamiento automático

La app envía el correo automáticamente 1 segundo después de abrirse (`root.after(1000, ...)`).
Esto es intencional y debe preservarse: permite ejecutarla desde el Task Scheduler de Windows
sin intervención del usuario.

## Configuración (config.json)

| Campo | Descripción |
|---|---|
| `destinatarios` | Lista de correos destino |
| `asunto` | Asunto del correo |
| `cuerpo` | Cuerpo con placeholders `[Mes en letras]` y `[año en numero]` |
| `auto_close` | Si se cierra automáticamente tras enviar |
| `auto_close_delay` | Segundos antes de cerrar (default: 60) |
| `email_method` | `"outlook"` o `"smtp"` |
| `smtp_config` | `{server, port, username, password}` |
| `language` | `"es"` o `"en"` |

## Log de actividad

El archivo `reminder_mail.log` se crea automáticamente junto al ejecutable (o en la raíz del proyecto en modo desarrollo). Contiene todos los eventos con timestamp para diagnóstico de errores.
