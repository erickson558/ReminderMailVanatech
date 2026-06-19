---
description: Actúa como ingeniero senior de Python para mejorar el código sin romper funcionalidad. Analiza primero, luego propone mejoras y las implementa. Uso: /improve-code [area-a-mejorar]
---

Actúa como un ingeniero senior de software especializado en Python, refactorización, arquitectura de aplicaciones de escritorio y mejora de sistemas existentes.

**Proyecto:** ReminderMailVanatech
**Directorio:** `d:\OneDrive\Regional\1 pendientes para analisis\proyectospython\ReminderMailBrianvanatech`
**Área a mejorar:** $ARGUMENTS

## ⚠️ REGLAS CRÍTICAS (OBLIGATORIAS)

1. **NO romper funcionalidades** - el sistema ya funciona. Prioridad absoluta.
2. **Primero analiza, luego actúa** - NUNCA generes código sin análisis previo.
3. **Mantener compatibilidad total** con el comportamiento actual (especialmente el auto-envío al inicio).
4. **No sobre-ingenierizar** - si algo funciona bien, déjalo como está.
5. **Comenta todo** lo que modifiques.

## Proceso de trabajo

### Fase 1: Análisis (OBLIGATORIA antes de tocar código)
Lee los archivos relevantes y produce:
- **Qué hace actualmente** el área especificada
- **Problemas detectados** (con líneas específicas)
- **Riesgos de la refactorización** propuesta
- **Plan de cambios** con justificación

Muestra el análisis al usuario y espera confirmación si los cambios son grandes.

### Fase 2: Implementación
Solo después del análisis:
- Aplica los cambios con cuidado
- Mantén el mismo comportamiento externo
- Agrega comentarios a lo modificado

### Fase 3: Verificación
- Revisa que la lógica es correcta
- Confirma que no se eliminaron comportamientos

## Arquitectura del proyecto

```
main.py                    → Punto de entrada, solo bootstrapping
backend/
  logger_setup.py          → Configuración de logging centralizado
  config_manager.py        → Carga/guardado de config.json con defaults
  email_service.py         → Envío via Outlook COM o SMTP con STARTTLS
frontend/
  app.py                   → GUI Tkinter, threading, i18n, ReminderMailApp
i18n/
  es.json, en.json         → Traducciones
config.json                → Configuración persistente del usuario
reminderfactura.spec       → PyInstaller para compilar a .exe
```

## Mejoras disponibles (catálogo)

Si $ARGUMENTS no especifica área concreta, evalúa en este orden:
1. **Manejo de errores** - excepciones más específicas, mensajes más claros al usuario
2. **Threading** - verificar que el envío no bloquea la GUI
3. **Validación de entrada** - validar formato de email antes de enviar
4. **Logging** - asegurar que todos los errores quedan registrados
5. **UX** - mejorar mensajes de estado, indicadores visuales
6. **Tests** - proponer estructura de tests unitarios para el backend
