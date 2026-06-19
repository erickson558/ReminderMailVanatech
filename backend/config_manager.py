"""
Módulo de gestión de configuración.

Responsabilidades:
  - Determinar la ruta correcta de config.json según el modo de ejecución.
  - Cargar la configuración con valores por defecto para claves faltantes.
  - Guardar la configuración actualizada en disco.

El archivo config.json se lee/escribe siempre junto al ejecutable (si está compilado)
o en la raíz del proyecto (si se ejecuta como script), garantizando persistencia
entre ejecuciones.
"""

import json
import os
import sys
from typing import Any, Dict

from backend.logger_setup import setup_logger

logger = setup_logger(__name__)

CONFIG_FILE = "config.json"

# ── Valores por defecto ────────────────────────────────────────────────────────
DEFAULTS: Dict[str, Any] = {
    "destinatarios": [],
    "asunto": "",
    "cuerpo": "",
    "auto_close": True,
    "auto_close_delay": 60,         # segundos antes de cerrar la app
    "email_method": "outlook",       # "outlook" (COM) o "smtp" (Hotmail/Gmail)
    "smtp_config": {
        "server": "smtp-mail.outlook.com",   # servidor para Hotmail/Outlook.com
        "port": 587,                          # puerto STARTTLS
        "username": "",                       # correo completo del remitente
        "password": ""                        # contraseña o app password
    },
    "language": "es"                 # idioma de la interfaz: "es" o "en"
}


def _get_project_root() -> str:
    """
    Devuelve la ruta raíz del proyecto.

    - Ejecutable compilado: directorio que contiene el .exe.
    - Script Python: dos niveles arriba de backend/ (→ project_root/).
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def get_config_path() -> str:
    """Devuelve la ruta absoluta a config.json."""
    return os.path.join(_get_project_root(), CONFIG_FILE)


def load_config() -> Dict[str, Any]:
    """
    Carga config.json y aplica valores por defecto para claves ausentes.

    Si el archivo no existe o está corrupto, devuelve la configuración
    con todos los valores por defecto sin lanzar excepción.

    Returns:
        Diccionario con la configuración completa del sistema.
    """
    config: Dict[str, Any] = {}
    config_path = get_config_path()

    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            logger.info("Configuración cargada desde: %s", config_path)
        except (json.JSONDecodeError, IOError) as exc:
            logger.error("Error al leer config.json (%s). Usando valores por defecto.", exc)
    else:
        logger.warning("config.json no encontrado en '%s'. Se usarán valores por defecto.", config_path)

    # Aplicar valores por defecto solo para claves ausentes (preservar los datos del usuario)
    for key, default in DEFAULTS.items():
        if key not in config:
            config[key] = default
        elif isinstance(default, dict):
            # Para claves anidadas (ej: smtp_config), completar sub-claves faltantes
            for sub_key, sub_default in default.items():
                config[key].setdefault(sub_key, sub_default)

    return config


def save_config(config: Dict[str, Any]) -> bool:
    """
    Serializa y guarda la configuración en config.json.

    Args:
        config: Diccionario con todos los parámetros a persistir.

    Returns:
        True si el guardado fue exitoso, False si hubo un error de I/O.
    """
    config_path = get_config_path()
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        logger.info("Configuración guardada en: %s", config_path)
        return True
    except (IOError, OSError) as exc:
        logger.error("No se pudo guardar config.json: %s", exc)
        return False
