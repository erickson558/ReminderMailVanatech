---
description: Agrega comentarios explicativos a un archivo Python del proyecto. Explica qué hace cada parte del código con docstrings y comentarios inline. Uso: /comment-code [nombre-del-archivo]
---

Vas a documentar el código del proyecto ReminderMailVanatech.

**Archivo a documentar:** $ARGUMENTS (si no se especifica, documenta todos los archivos Python del proyecto)

**Directorio del proyecto:** `d:\OneDrive\Regional\1 pendientes para analisis\proyectospython\ReminderMailBrianvanatech`

## Proceso

1. **Lee el archivo completo** antes de modificar nada.
2. **Entiende la lógica** - traza el flujo de ejecución.
3. **Agrega documentación** sin cambiar ninguna línea de código funcional.
4. **Verifica** que el archivo sigue siendo sintácticamente correcto.

## Qué documentar

### Módulos
- Propósito general del archivo
- Lista de lo que exporta
- Dependencias importantes
- Consideraciones de uso

### Clases
- Propósito y responsabilidad
- Patrón de diseño aplicado (si aplica)
- Ciclo de vida de la instancia

### Funciones y métodos
- Descripción de lo que hace
- Todos los parámetros con tipos y valores esperados
- Valor de retorno
- Excepciones que puede lanzar
- Efectos secundarios importantes

### Bloques de código complejos
- Comentar el "por qué" cuando la lógica no es obvia
- Señalar workarounds, restricciones de threading, o invariantes que se mantienen

## Reglas estrictas

- **NUNCA** cambiar la lógica, solo agregar comentarios y docstrings.
- **NUNCA** renombrar variables o funciones.
- **NUNCA** reorganizar el código.
- Los comentarios en **español**.
- Comentar el WHY, no el WHAT (el código ya dice qué hace).
- No comentar cosas obvias como `# suma 1 al contador`.

## Archivos disponibles

- `main.py`
- `backend/logger_setup.py`
- `backend/config_manager.py`
- `backend/email_service.py`
- `frontend/app.py`

Si $ARGUMENTS está vacío, documenta todos los archivos en el orden listado.
