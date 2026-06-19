"""
Punto de entrada principal de ReminderMailVanatech.

Responsabilidades:
  - Garantizar que el directorio raíz del proyecto esté en sys.path
    para que los paquetes 'backend' y 'frontend' sean importables.
  - Invocar run_app() que crea la ventana de Tkinter y arranca el bucle de eventos.

No contiene lógica de negocio: actúa solo como iniciador (bootstrapper).
"""

import os
import sys

# Agregar la raíz del proyecto al path de Python.
# Necesario cuando el script se ejecuta desde un directorio diferente
# o cuando PyInstaller lo empaqueta como ejecutable.
_root = os.path.dirname(os.path.abspath(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)

from frontend.app import run_app   # noqa: E402 – importación después de path setup

if __name__ == "__main__":
    run_app()
