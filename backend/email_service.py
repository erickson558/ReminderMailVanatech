"""
Módulo de envío de correos electrónicos.

Soporta dos métodos de envío configurables:

  1. Outlook COM (win32com)
     - Requiere Microsoft Outlook instalado y configurado en el equipo.
     - Funciona con cuentas Exchange, Microsoft 365 corporativo y Outlook.com
       siempre que Outlook las tenga añadidas como perfil.
     - Ventaja: no necesita guardar contraseña en la configuración.

  2. SMTP con STARTTLS
     - Funciona con Hotmail (@hotmail.com, @outlook.com) y Gmail.
     - NO requiere Outlook instalado.
     - Requiere usuario + contraseña (o App Password si la cuenta tiene 2FA activo).
     - Hotmail / Outlook.com: servidor smtp-mail.outlook.com, puerto 587.
     - Gmail: servidor smtp.gmail.com, puerto 587 (requiere App Password con 2FA).

Función pública principal:
    send_email(method, from_account, recipients, subject, body, smtp_config)

Todas las funciones registran su actividad en el logger del módulo.
"""

import datetime
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional

from backend.logger_setup import setup_logger

logger = setup_logger(__name__)

# ── Nombres de meses en español para el reemplazo de placeholders ─────────────
_MESES_ES: Dict[int, str] = {
    1: "enero",     2: "febrero",  3: "marzo",     4: "abril",
    5: "mayo",      6: "junio",    7: "julio",      8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
}


# ── Utilidades ─────────────────────────────────────────────────────────────────

def apply_placeholders(text: str) -> str:
    """
    Sustituye marcadores dinámicos en el texto del correo por valores reales.

    Marcadores soportados:
      [Mes en letras]  → Nombre completo del mes actual en español (ej: "Junio").
      [año en numero]  → Año actual como texto de 4 dígitos (ej: "2026").

    Args:
        text: Texto original que puede contener los marcadores.

    Returns:
        Texto con los marcadores reemplazados por sus valores actuales.
    """
    now = datetime.datetime.now()
    month_name = _MESES_ES[now.month].capitalize()  # primera letra mayúscula
    year_str = str(now.year)
    return (
        text
        .replace("[Mes en letras]", month_name)
        .replace("[año en numero]", year_str)
    )


def normalize_recipients(recipients: List[str]) -> List[str]:
    """
    Limpia y deduplica destinatarios preservando el orden original.

    Acepta entradas individuales o cadenas separadas por coma/punto y coma
    para tolerar ediciones manuales en config.json.
    """
    normalized: List[str] = []
    seen = set()

    for recipient in recipients:
        for chunk in recipient.replace(";", ",").split(","):
            candidate = chunk.strip()
            if not candidate:
                continue

            lowered = candidate.lower()
            if lowered in seen:
                continue

            seen.add(lowered)
            normalized.append(candidate)

    return normalized


def _populate_outlook_recipients(mail, recipients: List[str]) -> None:
    """Agrega y resuelve cada destinatario en el correo COM de Outlook."""
    unresolved: List[str] = []

    for address in normalize_recipients(recipients):
        outlook_recipient = mail.Recipients.Add(address)
        try:
            resolved = bool(outlook_recipient.Resolve())
        except Exception:
            resolved = False

        if not resolved:
            unresolved.append(address)

    if unresolved:
        raise ValueError(
            "Outlook no pudo resolver estos destinatarios: "
            + ", ".join(unresolved)
        )

    if not mail.Recipients.ResolveAll():
        raise ValueError("Outlook no pudo resolver la lista completa de destinatarios.")


# ── Método 1: Outlook COM ──────────────────────────────────────────────────────

def get_outlook_accounts() -> List[str]:
    """
    Consulta las cuentas SMTP registradas en el perfil de Outlook.

    Requiere que win32com y Microsoft Outlook estén disponibles.

    Returns:
        Lista de direcciones de correo (SmtpAddress) configuradas en Outlook.
        Lista vacía si Outlook no está disponible o no tiene cuentas.
    """
    try:
        import win32com.client as win32  # importación tardía: solo necesaria para este método
        outlook = win32.Dispatch('Outlook.Application')
        accounts = [acc.SmtpAddress for acc in outlook.Session.Accounts]
        logger.info("Cuentas Outlook detectadas: %s", accounts)
        return accounts
    except Exception as exc:
        logger.warning("No se pudo acceder a Outlook para listar cuentas: %s", exc)
        return []


def send_via_outlook(
    from_account: str,
    recipients: List[str],
    subject: str,
    body: str
) -> None:
    """
    Envía un correo usando la integración COM de Microsoft Outlook.

    Selecciona la cuenta de envío indicada en `from_account`. Si la cuenta
    no está en el perfil de Outlook, lanza ValueError.

    Los destinatarios se agregan uno por uno a la colección COM de Outlook
    para forzar su resolución y evitar que Outlook descarte direcciones de forma silenciosa.

    Args:
        from_account: Dirección SMTP exacta de la cuenta que envía (ej: "mi@outlook.com").
        recipients:   Lista de direcciones de correo destino.
        subject:      Asunto del mensaje.
        body:         Cuerpo en texto plano (sin HTML).

    Raises:
        RuntimeError: Si win32com (pywin32) no está instalado.
        ValueError:   Si `from_account` no se encuentra en el perfil de Outlook.
        Exception:    Cualquier otro error de la API COM de Outlook.
    """
    try:
        import pythoncom
        import win32com.client as win32
    except ImportError as exc:
        raise RuntimeError(
            "pywin32 no está instalado. Ejecuta: pip install pywin32\n"
            "Alternativa: cambia el método de envío a SMTP."
        ) from exc

    logger.info("Enviando via Outlook | from: %s | to: %s", from_account, recipients)

    pythoncom.CoInitialize()
    try:
        outlook = win32.Dispatch('Outlook.Application')
        mail = outlook.CreateItem(0)        # 0 = olMailItem (correo electrónico)
        mail.Subject = subject
        mail.Body = body

        # Buscar la cuenta remitente en el perfil de Outlook
        account_found = False
        for account in outlook.Session.Accounts:
            if account.SmtpAddress.lower() == from_account.lower():
                mail.SendUsingAccount = account
                account_found = True
                break

        if not account_found:
            raise ValueError(
                f"La cuenta '{from_account}' no está configurada en Outlook.\n"
                "Agrégala en Outlook → Archivo → Configuración de cuenta."
            )

        normalized_recipients = normalize_recipients(recipients)
        if not normalized_recipients:
            raise ValueError("No hay destinatarios válidos para el envío.")

        _populate_outlook_recipients(mail, normalized_recipients)
        mail.To = "; ".join(normalized_recipients)

        mail.Send()
        logger.info("Correo enviado exitosamente via Outlook desde '%s'.", from_account)
    finally:
        pythoncom.CoUninitialize()


# ── Método 2: SMTP / STARTTLS ──────────────────────────────────────────────────

def send_via_smtp(
    smtp_config: Dict,
    recipients: List[str],
    subject: str,
    body: str
) -> None:
    """
    Envía un correo usando SMTP con negociación STARTTLS (cifrado TLS en capa de transporte).

    Compatible con:
      - Hotmail / Outlook.com → smtp-mail.outlook.com:587
      - Gmail                 → smtp.gmail.com:587 (requiere App Password si tiene 2FA)
      - Cualquier servidor SMTP con STARTTLS

    Si la cuenta tiene verificación en dos pasos (2FA/MFA), se debe usar una
    "Contraseña de aplicación" (App Password) en lugar de la contraseña normal:
      - Hotmail: account.microsoft.com → Seguridad → Contraseñas de aplicación
      - Gmail:   myaccount.google.com  → Seguridad → Contraseñas de aplicación

    Args:
        smtp_config: Diccionario con las claves:
                       "server"   (str)  – servidor SMTP
                       "port"     (int)  – puerto (normalmente 587 para STARTTLS)
                       "username" (str)  – dirección de correo completa
                       "password" (str)  – contraseña o App Password
        recipients:  Lista de direcciones destino.
        subject:     Asunto del mensaje.
        body:        Cuerpo en texto plano.

    Raises:
        ValueError:           Si faltan username o password en smtp_config.
        smtplib.SMTPException: Si el servidor rechaza la conexión o las credenciales.
        TimeoutError:         Si no se puede conectar al servidor en 30 segundos.
    """
    username = smtp_config.get("username", "").strip()
    password = smtp_config.get("password", "").strip()
    server   = smtp_config.get("server",   "smtp-mail.outlook.com")
    port     = int(smtp_config.get("port", 587))
    normalized_recipients = normalize_recipients(recipients)

    if not username or not password:
        raise ValueError(
            "Se requieren usuario (username) y contraseña (password) para el método SMTP.\n"
            "Si tienes 2FA activo, genera una 'Contraseña de aplicación' en la configuración "
            "de seguridad de tu cuenta."
        )

    if not normalized_recipients:
        raise ValueError("No hay destinatarios válidos para el envío.")

    logger.info(
        "Enviando via SMTP | server: %s:%s | from: %s | to: %s",
        server, port, username, normalized_recipients
    )

    # Construir el mensaje MIME en UTF-8 para soportar caracteres especiales
    msg = MIMEMultipart()
    msg['From']    = username
    msg['To']      = "; ".join(normalized_recipients)
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    # Contexto SSL seguro con validación de certificados del servidor
    ssl_context = ssl.create_default_context()

    # Conectar con STARTTLS: primero conexión plana, luego upgrade a TLS
    with smtplib.SMTP(server, port, timeout=30) as conn:
        conn.ehlo()                         # presentar cliente al servidor
        conn.starttls(context=ssl_context)  # subir a canal cifrado
        conn.ehlo()                         # re-presentar sobre TLS
        conn.login(username, password)      # autenticar
        conn.sendmail(username, normalized_recipients, msg.as_string())

    logger.info("Correo enviado exitosamente via SMTP desde '%s'.", username)


# ── Función pública principal ──────────────────────────────────────────────────

def send_email(
    method: str,
    from_account: str,
    recipients: List[str],
    subject: str,
    body: str,
    smtp_config: Optional[Dict] = None
) -> None:
    """
    Envía un correo aplicando primero los placeholders dinámicos al cuerpo.

    Delega en `send_via_outlook` o `send_via_smtp` según el método elegido.

    Args:
        method:       "outlook" → usa Outlook COM | "smtp" → usa SMTP/STARTTLS.
        from_account: Cuenta remitente (Outlook) o username SMTP.
        recipients:   Lista de destinatarios.
        subject:      Asunto del correo.
        body:         Cuerpo con posibles placeholders [Mes en letras], [año en numero].
        smtp_config:  Configuración SMTP; obligatorio cuando method="smtp".

    Raises:
        ValueError: Si el método no es "outlook" ni "smtp", o falta smtp_config.
        Exception:  Cualquier error durante el envío (re-lanzado para manejo en la GUI).
    """
    recipients = normalize_recipients(recipients)

    # Resolver placeholders antes de enviar (ej: [Mes en letras] → "Junio")
    processed_body = apply_placeholders(body)

    if method == "outlook":
        send_via_outlook(from_account, recipients, subject, processed_body)

    elif method == "smtp":
        if smtp_config is None:
            raise ValueError("smtp_config es obligatorio cuando method='smtp'.")
        send_via_smtp(smtp_config, recipients, subject, processed_body)

    else:
        raise ValueError(
            f"Método de envío '{method}' no reconocido. Use 'outlook' o 'smtp'."
        )
