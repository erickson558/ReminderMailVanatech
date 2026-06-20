# SDD — Spec Driven Development
# ReminderMailVanatech

**Versión:** 2.0  
**Fecha:** 2026-06-19  
**Autor:** erickson558

---

## 1. Visión general

Sistema de recordatorio de factura que envía correos electrónicos automáticamente.
Diseñado para ejecutarse desde Windows Task Scheduler sin intervención del usuario.

---

## 2. Especificaciones funcionales

### 2.1 Envío de correo

| ID | Especificación | Estado |
|---|---|---|
| F-01 | El correo se envía automáticamente 1 segundo después de abrir la app | ✅ Implementado |
| F-02 | Soporte para envío via Outlook COM (requiere Outlook instalado) | ✅ Implementado |
| F-03 | Soporte para envío via SMTP/STARTTLS (Hotmail, Gmail, sin Outlook) | ✅ Implementado |
| F-04 | El remitente no aparece como destinatario (filtrado automático) | ✅ Implementado |
| F-05 | El cuerpo acepta placeholders `[Mes en letras]` y `[año en numero]` | ✅ Implementado |
| F-06 | Errores de envío se muestran en la barra de estado y en el log | ✅ Implementado |
| F-07 | El envío NO bloquea la interfaz gráfica (thread separado) | ✅ Implementado |

### 2.2 Gestión de destinatarios

| ID | Especificación | Estado |
|---|---|---|
| D-01 | Agregar destinatarios mediante diálogo de texto | ✅ Implementado |
| D-02 | Eliminar uno o varios destinatarios seleccionados | ✅ Implementado |
| D-03 | Lista de destinatarios persiste entre sesiones (config.json) | ✅ Implementado |
| D-04 | Validación de formato de email antes de agregar | 🔲 Pendiente |

### 2.3 Configuración

| ID | Especificación | Estado |
|---|---|---|
| C-01 | Configuración guardada en config.json junto al ejecutable | ✅ Implementado |
| C-02 | Valores por defecto para todos los campos si no hay config.json | ✅ Implementado |
| C-03 | Selector de método de envío: Outlook vs SMTP | ✅ Implementado |
| C-04 | Configuración SMTP: servidor, puerto, usuario, contraseña | ✅ Implementado |
| C-05 | Cierre automático configurable (activar/desactivar + delay en segundos) | ✅ Implementado |
| C-06 | Selección de idioma persistente | ✅ Implementado |

### 2.4 Interfaz gráfica

| ID | Especificación | Estado |
|---|---|---|
| G-01 | GUI Tkinter sin congelamiento durante operaciones (threading) | ✅ Implementado |
| G-02 | Barra de estado con mensajes de éxito (verde) y error (rojo) | ✅ Implementado |
| G-03 | Panel SMTP visible solo cuando se selecciona método SMTP | ✅ Implementado |
| G-04 | Botón Enviar deshabilitado durante el envío (evita duplicados) | ✅ Implementado |
| G-05 | Botón "Cómprame una cerveza" con enlace PayPal | ✅ Implementado |
| G-06 | Selector de idioma integrado en la ventana principal | ✅ Implementado |

### 2.5 Internacionalización (i18n)

| ID | Especificación | Estado |
|---|---|---|
| I-01 | Todos los textos de la GUI en archivos JSON separados por idioma | ✅ Implementado |
| I-02 | Soporte español (es.json) | ✅ Implementado |
| I-03 | Soporte inglés (en.json) | ✅ Implementado |
| I-04 | Cambio de idioma en caliente sin perder datos del formulario | ✅ Implementado |
| I-05 | Fallback al español si el archivo de idioma no existe | ✅ Implementado |

### 2.6 Logging y diagnóstico

| ID | Especificación | Estado |
|---|---|---|
| L-01 | Log a archivo `reminder_mail.log` junto al ejecutable | ✅ Implementado |
| L-02 | Niveles: DEBUG (archivo), INFO (consola en desarrollo) | ✅ Implementado |
| L-03 | Formato: `timestamp | nivel | módulo | mensaje` | ✅ Implementado |
| L-04 | Sin consola visible en el ejecutable compilado | ✅ Implementado |

### 2.7 Compilación

| ID | Especificación | Estado |
|---|---|---|
| P-01 | Compilar a .exe con PyInstaller | ✅ Implementado |
| P-02 | Ejecutable sin ventana de consola | ✅ Implementado |
| P-03 | Ícono reminderagua.ico en el ejecutable | ✅ Implementado |
| P-04 | Archivos i18n empaquetados dentro del .exe | ✅ Implementado |
| P-05 | config.json NO empaquetado (persiste junto al .exe) | ✅ Implementado |
| P-06 | La recompilación deja `reminderfacturavanatech.exe` en la raíz del proyecto, junto a `main.py`/`config.json` | ✅ Implementado |

---

## 3. Especificaciones técnicas

### 3.1 Método SMTP (Hotmail)

```
Servidor:  smtp-mail.outlook.com
Puerto:    587
Seguridad: STARTTLS (upgrade de conexión plana a cifrada)
Auth:      LOGIN (usuario + contraseña o App Password)
Encoding:  UTF-8 en el cuerpo del mensaje
```

**Nota 2FA:** Si la cuenta Hotmail tiene verificación en dos pasos activada,
se debe usar una "Contraseña de aplicación" generada en:
`account.microsoft.com → Seguridad → Contraseñas de aplicación`

### 3.2 Método Outlook COM

```
Librería:  win32com.client (pywin32)
Objeto:    outlook.Application.CreateItem(0) → MailItem
Cuenta:    Seleccionada por SmtpAddress del perfil de Outlook
Requires:  Microsoft Outlook instalado y configurado en el equipo
```

### 3.3 Threading

El envío de correo se ejecuta en un `threading.Thread(daemon=True)`.
La GUI se actualiza exclusivamente via `root.after(0, callback)` para garantizar
thread-safety (Tkinter no es thread-safe por diseño).

### 3.4 Placeholders dinámicos

| Placeholder | Valor | Ejemplo |
|---|---|---|
| `[Mes en letras]` | Nombre del mes actual en español | `Junio` |
| `[año en numero]` | Año actual como 4 dígitos | `2026` |

---

## 4. Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                    main.py (bootstrapper)               │
│              sys.path setup + run_app()                 │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              frontend/app.py (GUI Layer)                │
│                   ReminderMailApp                       │
│  - Tkinter widgets                                      │
│  - i18n (load_translations)                             │
│  - Threading para envío non-blocking                    │
│  - root.after() para thread-safe UI updates             │
└──────┬────────────────────────┬────────────────────────┘
       │                        │
       ▼                        ▼
┌──────────────┐    ┌───────────────────────────────────┐
│   backend/   │    │          backend/                 │
│ config_      │    │       email_service.py            │
│ manager.py   │    │                                   │
│              │    │  send_via_outlook() → win32com     │
│ load_config()│    │  send_via_smtp()   → smtplib       │
│ save_config()│    │  apply_placeholders()             │
└──────────────┘    └───────────────────────────────────┘
       │
       ▼
┌──────────────┐
│ config.json  │ (junto al .exe o raíz del proyecto)
└──────────────┘
```

---

## 5. Pendientes / Backlog

| ID | Tarea | Prioridad |
|---|---|---|
| D-04 | Validar formato de email (regex) al agregar destinatario | Media |
| T-01 | Tests unitarios para backend/email_service.py | Alta |
| T-02 | Tests unitarios para backend/config_manager.py | Alta |
| U-01 | Agregar soporte para correo en formato HTML | Baja |
| U-02 | Preview del correo antes de enviar | Baja |
| U-03 | Agregar idioma Portugués | Baja |

---

## 6. Historial de versiones

| Versión | Fecha | Cambios |
|---|---|---|
| 1.0 | 2025 | Versión inicial: GUI monolítica, solo Outlook COM |
| 2.0 | 2026-06-19 | Refactorización completa: backend/frontend separados, SMTP para Hotmail, i18n, threading, logging, SDD, agentes Claude Code |
