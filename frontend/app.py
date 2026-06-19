"""
Módulo de interfaz gráfica de usuario (GUI).

Implementa la clase ReminderMailApp que encapsula toda la lógica visual.

Principios aplicados:
  - Separación frontend/backend: la GUI solo llama a funciones del backend,
    nunca maneja lógica de negocio directamente.
  - No-blocking UI: el envío de correo corre en un hilo daemon (threading.Thread)
    y actualiza la GUI con root.after() para garantizar thread-safety.
  - Internacionalización (i18n): todos los textos visibles provienen de archivos
    JSON en i18n/ (es.json, en.json), seleccionables desde la propia interfaz.
  - Reconexión de idioma: cambiar idioma destruye y reconstruye los widgets
    sin perder los datos ingresados por el usuario.
"""

import json
import os
import sys
import threading
import webbrowser
import tkinter as tk
from tkinter import simpledialog, ttk
from typing import Dict, Optional

from backend.config_manager import load_config, save_config
from backend.email_service import get_outlook_accounts, send_email
from backend.logger_setup import setup_logger

logger = setup_logger(__name__)

# URL del botón de donación PayPal
_DONATE_URL = "https://www.paypal.com/donate/?hosted_button_id=ZABFRXC2P3JQN"


# ── Utilidades de i18n ─────────────────────────────────────────────────────────

def _get_i18n_dir() -> str:
    """
    Devuelve la ruta al directorio i18n con los archivos de traducción.

    - Ejecutable compilado: sys._MEIPASS/i18n (extraído por PyInstaller).
    - Script Python: project_root/i18n (dos niveles arriba de frontend/).
    """
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'i18n')  # type: ignore[attr-defined]
    # frontend/app.py → frontend/ → project_root/ → i18n/
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'i18n'))


def load_translations(lang: str) -> Dict[str, str]:
    """
    Carga el diccionario de traducciones para el idioma indicado.

    Si el archivo no existe, intenta cargar el español como fallback.
    Si tampoco existe, devuelve un diccionario vacío (las claves se mostrarán como texto).

    Args:
        lang: Código ISO del idioma ('es', 'en').

    Returns:
        Diccionario {clave: texto_traducido}.
    """
    i18n_dir = _get_i18n_dir()
    candidates = [
        os.path.join(i18n_dir, f"{lang}.json"),
        os.path.join(i18n_dir, "es.json"),   # fallback
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    logger.debug("Traducciones cargadas desde: %s", path)
                    return json.load(f)
            except Exception as exc:
                logger.error("Error al cargar traducciones '%s': %s", path, exc)
    logger.warning("No se encontró ningún archivo de traducción en '%s'.", i18n_dir)
    return {}


# ── Clase principal de la aplicación ──────────────────────────────────────────

class ReminderMailApp:
    """
    Aplicación de recordatorio de correo con GUI Tkinter.

    Flujo de trabajo:
      1. __init__ carga configuración y construye la GUI.
      2. 1 segundo después del inicio se dispara el envío automático.
      3. El usuario puede ajustar campos, guardar configuración o enviar manualmente.
      4. El envío se ejecuta en un hilo de fondo (no bloquea la GUI).
    """

    def __init__(self, root: tk.Tk) -> None:
        """
        Inicializa la aplicación.

        Carga la configuración desde config.json, prepara las traducciones
        y construye la interfaz gráfica completa.

        Args:
            root: Ventana principal de Tkinter creada por el punto de entrada.
        """
        self.root = root
        self.config = load_config()

        # Estado de envío: evita disparar envíos concurrentes
        self._sending = False

        # Cargar idioma configurado
        self._lang: str = self.config.get("language", "es")
        self._t: Dict[str, str] = load_translations(self._lang)

        # Construir todos los widgets de la interfaz
        self._build_ui()

        # Disparar envío automático 1 segundo tras el inicio (comportamiento original)
        self.root.after(1000, self._btn_enviar.invoke)

        logger.info("Aplicación iniciada | idioma: %s | método: %s",
                    self._lang, self.config.get("email_method", "outlook"))

    # ── API de traducción ──────────────────────────────────────────────────────

    def t(self, key: str, **kwargs) -> str:
        """
        Devuelve el texto traducido para la clave dada en el idioma activo.

        Si la clave no existe, devuelve la propia clave como texto de emergencia.
        Admite formateo con variables: t("status_closing", delay=60).

        Args:
            key:    Clave del diccionario de traducción.
            **kwargs: Variables para formatear el texto (placeholders {var}).

        Returns:
            Texto traducido y formateado.
        """
        text = self._t.get(key, key)
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, ValueError):
                pass  # Si el formato falla, devolver el texto sin formatear
        return text

    # ── Estado de la barra inferior ────────────────────────────────────────────

    def update_status(self, message: str, color: str = "black") -> None:
        """
        Actualiza el mensaje de la barra de estado.

        Debe llamarse siempre desde el hilo principal de Tkinter.
        Para llamar desde un hilo de fondo, usar root.after(0, update_status, ...).

        Args:
            message: Texto a mostrar en la barra.
            color:   Color del texto ('black', 'green', 'red', 'orange').
        """
        self._status_label.config(text=message, fg=color)
        logger.debug("Estado actualizado: [%s] %s", color, message)

    # ── Construcción de la interfaz ────────────────────────────────────────────

    def _build_ui(self) -> None:
        """
        Construye y empaqueta todos los widgets de la ventana principal.

        Se puede llamar más de una vez (al cambiar idioma): destruye todos
        los widgets existentes antes de reconstruir, preservando los datos
        del formulario a través de self.config.
        """
        # Destruir widgets existentes (si los hay, al cambiar idioma)
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.title(self.t("title"))
        self.root.resizable(False, False)

        # ── 1. Selector de idioma ──────────────────────────────────────
        frame_lang = tk.Frame(self.root)
        frame_lang.pack(fill=tk.X, padx=10, pady=(5, 0))

        tk.Label(frame_lang, text=self.t("language")).pack(side=tk.LEFT)

        for code, label in [("es", "Español"), ("en", "English")]:
            rb = tk.Radiobutton(
                frame_lang, text=label, value=code,
                command=lambda c=code: self._change_language(c)
            )
            rb.pack(side=tk.LEFT, padx=5)
            if self._lang == code:
                rb.select()

        # ── 2. Lista de destinatarios ──────────────────────────────────
        frame_dest = tk.LabelFrame(self.root, text=self.t("recipients"))
        frame_dest.pack(pady=5, fill=tk.X, padx=10)

        self._listbox = tk.Listbox(frame_dest, width=55, height=5, selectmode=tk.EXTENDED)
        for addr in self.config.get("destinatarios", []):
            self._listbox.insert(tk.END, addr)
        self._listbox.pack(pady=5, padx=10)

        frame_dest_btns = tk.Frame(frame_dest)
        frame_dest_btns.pack(pady=(0, 5))

        tk.Button(
            frame_dest_btns, text=self.t("add"), width=15,
            command=self._agregar_destinatario
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            frame_dest_btns, text=self.t("remove"), width=15,
            command=self._eliminar_destinatario
        ).pack(side=tk.LEFT, padx=5)

        # ── 3. Asunto ──────────────────────────────────────────────────
        tk.Label(self.root, text=self.t("subject")).pack(pady=(5, 0))
        self._entry_asunto = tk.Entry(self.root, width=57)
        self._entry_asunto.insert(0, self.config.get("asunto", ""))
        self._entry_asunto.pack(pady=5, padx=10)

        # ── 4. Cuerpo del correo ───────────────────────────────────────
        tk.Label(self.root, text=self.t("body")).pack(pady=(5, 0))
        self._text_cuerpo = tk.Text(self.root, width=57, height=10)
        self._text_cuerpo.insert("1.0", self.config.get("cuerpo", ""))
        self._text_cuerpo.pack(pady=5, padx=10)

        # ── 5. Configuración de la cuenta de envío ────────────────────
        frame_cuenta = tk.LabelFrame(self.root, text=self.t("sending_account"))
        frame_cuenta.pack(padx=10, pady=5, fill="both")

        # Selector de método: Outlook COM vs SMTP
        frame_method = tk.Frame(frame_cuenta)
        frame_method.pack(anchor="w", padx=10, pady=5)

        tk.Label(frame_method, text=self.t("method")).pack(side=tk.LEFT)

        self._method_var = tk.StringVar(value=self.config.get("email_method", "outlook"))

        tk.Radiobutton(
            frame_method, text=self.t("method_outlook"), value="outlook",
            variable=self._method_var, command=self._on_method_change
        ).pack(side=tk.LEFT, padx=8)

        tk.Radiobutton(
            frame_method, text=self.t("method_smtp"), value="smtp",
            variable=self._method_var, command=self._on_method_change
        ).pack(side=tk.LEFT)

        # Combobox con cuentas de Outlook (solo visible en modo Outlook)
        tk.Label(frame_cuenta, text=self.t("select_account")).pack(anchor="w", padx=10)

        cuentas = []
        try:
            cuentas = get_outlook_accounts()
        except Exception:
            pass

        self._combobox_cuenta = ttk.Combobox(
            frame_cuenta, values=cuentas, state="readonly", width=50
        )
        if cuentas:
            # Pre-seleccionar la cuenta guardada si está disponible
            saved_account = self.config.get("smtp_config", {}).get("username", "")
            try:
                idx = [c.lower() for c in cuentas].index(saved_account.lower())
                self._combobox_cuenta.current(idx)
            except ValueError:
                self._combobox_cuenta.current(0)
        self._combobox_cuenta.pack(anchor="w", padx=10, pady=(0, 5))

        # ── Panel SMTP (visible solo cuando método = smtp) ─────────────
        self._frame_smtp = tk.LabelFrame(frame_cuenta, text=self.t("smtp_settings"))

        smtp_cfg = self.config.get("smtp_config", {})

        # Fila helper para crear pares (label, entry) de forma consistente
        def _smtp_row(parent, label_key: str, default: str, show: str = "") -> tk.Entry:
            """Crea una fila label+entry dentro del panel SMTP y devuelve el Entry."""
            row = tk.Frame(parent)
            row.pack(fill=tk.X, padx=10, pady=2)
            tk.Label(row, text=self.t(label_key), width=20, anchor="w").pack(side=tk.LEFT)
            entry = tk.Entry(row, width=32, show=show)
            entry.insert(0, default)
            entry.pack(side=tk.LEFT)
            return entry

        self._entry_smtp_server = _smtp_row(
            self._frame_smtp, "smtp_server", smtp_cfg.get("server", "smtp-mail.outlook.com")
        )
        self._entry_smtp_port = _smtp_row(
            self._frame_smtp, "smtp_port", str(smtp_cfg.get("port", 587))
        )
        self._entry_smtp_user = _smtp_row(
            self._frame_smtp, "smtp_user", smtp_cfg.get("username", "")
        )
        self._entry_smtp_pass = _smtp_row(
            self._frame_smtp, "smtp_pass", smtp_cfg.get("password", ""), show="*"
        )
        # Espacio inferior dentro del panel SMTP
        tk.Frame(self._frame_smtp).pack(pady=3)

        # Mostrar/ocultar panel SMTP según el método guardado
        self._on_method_change()

        # ── 6. Cierre automático ───────────────────────────────────────
        frame_ac = tk.LabelFrame(self.root, text=self.t("auto_close"))
        frame_ac.pack(padx=10, pady=5, fill="both")

        self._auto_close_var = tk.BooleanVar(value=self.config.get("auto_close", True))
        tk.Checkbutton(
            frame_ac, text=self.t("auto_close_check"),
            variable=self._auto_close_var
        ).pack(anchor="w", padx=10, pady=5)

        self._auto_close_delay_var = tk.StringVar(
            value=str(self.config.get("auto_close_delay", 60))
        )
        tk.Label(frame_ac, text=self.t("auto_close_delay")).pack(anchor="w", padx=10)
        tk.Entry(
            frame_ac, textvariable=self._auto_close_delay_var, width=8
        ).pack(anchor="w", padx=10, pady=(0, 8))

        # ── 7. Botones de acción ───────────────────────────────────────
        frame_btns = tk.Frame(self.root)
        frame_btns.pack(pady=10)

        # Botón Enviar (se referencia como self._btn_enviar para auto-disparo al inicio)
        self._btn_enviar = tk.Button(
            frame_btns, text=self.t("send"), width=16,
            command=self._enviar_correo_async,
            bg="#28a745", fg="white", font=("Arial", 9, "bold")
        )
        self._btn_enviar.pack(side=tk.LEFT, padx=4)

        tk.Button(
            frame_btns, text=self.t("save_config"), width=18,
            command=self._save_config
        ).pack(side=tk.LEFT, padx=4)

        tk.Button(
            frame_btns, text=self.t("exit"), width=12,
            command=self.root.destroy
        ).pack(side=tk.LEFT, padx=4)

        # Botón de donación PayPal (azul corporativo)
        tk.Button(
            frame_btns, text=self.t("buy_coffee"), width=20,
            bg="#003087", fg="white", font=("Arial", 9, "bold"),
            command=lambda: webbrowser.open(_DONATE_URL)
        ).pack(side=tk.LEFT, padx=4)

        # ── 8. Barra de estado ─────────────────────────────────────────
        self._status_label = tk.Label(
            self.root, text="", bd=1, relief=tk.SUNKEN, anchor=tk.W, padx=5
        )
        self._status_label.pack(side=tk.BOTTOM, fill=tk.X)

    # ── Handlers de eventos de la GUI ──────────────────────────────────────────

    def _change_language(self, lang: str) -> None:
        """
        Cambia el idioma de la interfaz y reconstruye todos los widgets.

        Los datos actualmente ingresados (destinatarios, asunto, cuerpo, etc.)
        se guardan en self.config antes de reconstruir para no perderlos.

        Args:
            lang: Código del nuevo idioma ('es' o 'en').
        """
        # Capturar datos actuales del formulario antes de destruir los widgets
        self.config.update(self._collect_form_data())
        self._lang = lang
        self.config["language"] = lang
        self._t = load_translations(lang)
        self._build_ui()
        logger.info("Idioma cambiado a: %s", lang)

    def _on_method_change(self) -> None:
        """
        Muestra u oculta el panel de configuración SMTP según el método elegido.

        - Outlook: muestra combobox de cuentas, oculta panel SMTP.
        - SMTP:    oculta combobox, muestra panel SMTP con campos de credenciales.
        """
        if self._method_var.get() == "smtp":
            self._combobox_cuenta.config(state="disabled")
            self._frame_smtp.pack(fill="both", padx=10, pady=(0, 5))
        else:
            self._frame_smtp.pack_forget()
            self._combobox_cuenta.config(state="readonly")

    def _agregar_destinatario(self) -> None:
        """Abre un diálogo para ingresar un nuevo destinatario y lo agrega a la lista."""
        nuevo = simpledialog.askstring(
            self.t("dialog_add_recipient"),
            self.t("dialog_add_recipient_prompt"),
            parent=self.root
        )
        if nuevo and nuevo.strip():
            self._listbox.insert(tk.END, nuevo.strip())
            self.update_status(self.t("status_added"), "green")

    def _eliminar_destinatario(self) -> None:
        """Elimina los destinatarios seleccionados en la lista."""
        seleccion = self._listbox.curselection()
        if not seleccion:
            self.update_status(self.t("status_select_recipient"), "red")
            return
        # Eliminar de abajo hacia arriba para no alterar los índices
        for idx in reversed(seleccion):
            self._listbox.delete(idx)
        self.update_status(self.t("status_removed"), "green")

    # ── Recolección de datos del formulario ────────────────────────────────────

    def _collect_form_data(self) -> dict:
        """
        Recolecta todos los valores actuales de los widgets del formulario.

        IMPORTANTE: debe llamarse siempre desde el hilo principal de Tkinter
        (los widgets solo son accesibles de forma segura desde el hilo que los creó).

        Returns:
            Diccionario con todos los campos del formulario listos para persistir.
        """
        try:
            port = int(self._entry_smtp_port.get().strip() or 587)
        except ValueError:
            port = 587

        try:
            delay = int(self._auto_close_delay_var.get() or 60)
        except ValueError:
            delay = 60

        return {
            "destinatarios": list(self._listbox.get(0, tk.END)),
            "asunto":         self._entry_asunto.get().strip(),
            "cuerpo":         self._text_cuerpo.get("1.0", tk.END).strip(),
            "auto_close":     self._auto_close_var.get(),
            "auto_close_delay": delay,
            "email_method":   self._method_var.get(),
            "smtp_config": {
                "server":   self._entry_smtp_server.get().strip(),
                "port":     port,
                "username": self._entry_smtp_user.get().strip(),
                "password": self._entry_smtp_pass.get().strip(),
            },
            "language": self._lang,
            # Cuenta Outlook seleccionada: solo relevante para método "outlook"
            "_outlook_account": self._combobox_cuenta.get()
        }

    def _save_config(self) -> None:
        """Guarda la configuración actual del formulario en config.json."""
        data = self._collect_form_data()
        # Eliminar clave auxiliar antes de persistir (no debe ir al JSON)
        data.pop("_outlook_account", None)

        if save_config(data):
            self.config = data
            self.update_status(self.t("status_saved"), "green")
        else:
            self.update_status(self.t("error_save", error="ver reminder_mail.log"), "red")

    # ── Envío de correo (non-blocking) ─────────────────────────────────────────

    def _enviar_correo_async(self) -> None:
        """
        Valida los datos del formulario y lanza el envío en un hilo de fondo.

        Deshabilita el botón Enviar mientras el hilo trabaja para evitar
        envíos duplicados. El estado de la GUI se actualiza via root.after().
        """
        # Guardia: no permitir envíos concurrentes
        if self._sending:
            return

        # Recolectar datos en el hilo principal ANTES de lanzar el hilo
        form_data = self._collect_form_data()

        # Validar que hay al menos un destinatario
        if not form_data["destinatarios"]:
            self.update_status(self.t("status_no_recipients"), "red")
            return

        # Preparar el campo from_account según el método (acceso thread-safe aquí)
        method = form_data["email_method"]
        form_data["from_account"] = (
            form_data["_outlook_account"] if method == "outlook"
            else form_data["smtp_config"]["username"]
        )
        form_data.pop("_outlook_account", None)

        # Bloquear UI y lanzar hilo de fondo
        self._sending = True
        self._btn_enviar.config(state=tk.DISABLED)
        self.update_status(self.t("status_sending"), "orange")

        thread = threading.Thread(
            target=self._enviar_correo_thread,
            args=(form_data,),
            daemon=True  # daemon: el hilo no impedirá cerrar la app
        )
        thread.start()

    def _enviar_correo_thread(self, form_data: dict) -> None:
        """
        Ejecuta el envío de correo en un hilo de fondo.

        No toca widgets de Tkinter directamente: usa root.after(0, callback)
        para devolver el control al hilo principal de la GUI.

        Args:
            form_data: Datos completos del formulario capturados antes de iniciar el hilo.
        """
        try:
            send_email(
                method=form_data["email_method"],
                from_account=form_data["from_account"],
                recipients=form_data["destinatarios"],
                subject=form_data["asunto"],
                body=form_data["cuerpo"],
                smtp_config=form_data.get("smtp_config")
            )
            # Éxito: notificar al hilo principal
            self.root.after(0, self._on_send_success, form_data)
        except Exception as exc:
            logger.error("Error al enviar correo: %s", exc)
            # Error: notificar al hilo principal con el mensaje de error
            self.root.after(0, self._on_send_error, str(exc))

    def _on_send_success(self, form_data: dict) -> None:
        """
        Callback ejecutado en el hilo principal tras un envío exitoso.

        Reactiva el botón Enviar y, si está habilitado el cierre automático,
        programa la destrucción de la ventana después del delay configurado.

        Args:
            form_data: Datos del formulario usados en el envío.
        """
        self._sending = False
        self._btn_enviar.config(state=tk.NORMAL)

        if form_data.get("auto_close"):
            delay: int = form_data.get("auto_close_delay", 60)
            self.update_status(self.t("status_closing", delay=delay), "green")
            # Programar cierre: delay en segundos → convertir a ms para root.after
            self.root.after(delay * 1000, self.root.destroy)
        else:
            self.update_status(self.t("status_sent"), "green")

    def _on_send_error(self, error_msg: str) -> None:
        """
        Callback ejecutado en el hilo principal tras un error de envío.

        Reactiva el botón Enviar y muestra el error en la barra de estado.

        Args:
            error_msg: Descripción del error para mostrar al usuario.
        """
        self._sending = False
        self._btn_enviar.config(state=tk.NORMAL)
        self.update_status(self.t("status_error", error=error_msg), "red")


# ── Punto de entrada del módulo ────────────────────────────────────────────────

def run_app() -> None:
    """
    Crea la ventana principal de Tkinter e inicia el bucle de eventos.

    Esta función es el único punto de entrada a la GUI y debe llamarse
    desde main.py (o desde el ejecutable compilado).
    """
    root = tk.Tk()
    _app = ReminderMailApp(root)   # noqa: F841 – la app se auto-registra con root
    root.mainloop()
