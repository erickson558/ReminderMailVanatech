"""
Módulo de configuración del sistema de logging.

Configura un logger con dos handlers:
  - FileHandler: escribe todos los niveles (DEBUG+) en reminder_mail.log junto al ejecutable/proyecto.
  - StreamHandler: muestra INFO+ en consola (solo en modo desarrollo, no en .exe).

Uso:
    from backend.logger_setup import setup_logger
    logger = setup_logger(__name__)
"""

import logging
import os
import sys


def _get_log_dir() -> str:
    """
    Determina el directorio donde se guardará el archivo de log.

    - Ejecutable compilado (.exe): directorio del .exe (persiste entre ejecuciones).
    - Script Python: raíz del proyecto (dos niveles arriba de backend/).
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    # backend/logger_setup.py  →  backend/  →  project_root/
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def setup_logger(name: str = "reminder_mail") -> logging.Logger:
    """
    Crea y devuelve un logger configurado para el módulo dado.

    Si el logger ya tiene handlers (llamada duplicada), lo devuelve tal cual
    para evitar handlers duplicados que generarían entradas repetidas en el log.

    Args:
        name: Nombre del logger, normalmente __name__ del módulo que lo invoca.

    Returns:
        logging.Logger listo para usar.
    """
    logger = logging.getLogger(name)

    # Evitar agregar handlers duplicados si el logger ya fue configurado
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Formato unificado: timestamp | nivel | módulo | mensaje
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # ── Handler de archivo (DEBUG+, siempre activo) ────────────────────
    log_file = os.path.join(_get_log_dir(), 'reminder_mail.log')
    try:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except (IOError, OSError):
        pass  # Sin acceso al sistema de archivos: ignorar y continuar

    # ── Handler de consola (INFO+, solo en modo desarrollo) ───────────
    if not getattr(sys, 'frozen', False):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
