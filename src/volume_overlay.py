"""Indicador discreto sobre la barra de tareas: nivel de volumen y cambio de modo (icono + poco texto)."""

import ctypes
import ctypes.wintypes
import queue
import threading

_values = queue.Queue(maxsize=1)
_lock = threading.Lock()
_started = False

# Iconos de «Segoe MDL2 Assets» (incluida en Windows) para los iconos que ofrece la interfaz.
GLYPHS = {"target": "\uE765", "music": "\uE8D6", "mic": "\uE720", "clapperboard": "\uE714", "app-window": "\uE774",
          "brush": "\uE790", "code-xml": "\uE943", "gamepad-2": "\uE7FC", "pen-line": "\uE70F", "sliders-horizontal": "\uE713"}
GLYPHS.update({name: chr(code) for name, code in {"globe": 0xE774, "film": 0xE714, "terminal": 0xE756, "zap": 0xE945,
                                                 "message-circle": 0xE8BD, "notebook-pen": 0xE70F, "volume-2": 0xE767, "sparkles": 0xE734}.items()})
# Los iconos de marca no tienen glifo propio en Windows: se usa el del icono genérico más parecido.
_LIKE = {"music": ("spotify",), "gamepad-2": ("wow", "steam", "epic", "battlenet", "minecraft", "twitch"), "clapperboard": ("obs",), "film": ("vlc",),
         "message-circle": ("whatsapp", "telegram", "discord", "slack", "teams", "zoom"),
         "globe": ("chrome", "edge", "firefox", "opera", "brave", "google"), "sparkles": ("claude", "chatgpt"),
         "notebook-pen": ("word", "excel", "powerpoint", "office", "notion", "obsidian"), "code-xml": ("vscode",),
         "brush": ("adobe", "figma", "davinci", "blender")}
GLYPHS.update({brand: GLYPHS[base] for base, brands in _LIKE.items() for brand in brands})
W, H = 280, 56
MARGIN = 16


def notice_origin(work, width, height, margin=MARGIN):
    """Esquina inferior derecha del área útil (justo encima de la barra de tareas y de la bandeja)."""
    _left, _top, right, bottom = work
    return right - width - margin, bottom - height - margin


def _work_area(user32, fallback):
    rect = ctypes.wintypes.RECT()
    if user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0):   # SPI_GETWORKAREA
        return rect.left, rect.top, rect.right, rect.bottom
    return fallback


def _post(item):
    global _started
    with _lock:
        if not _started:
            _started = True
            threading.Thread(target=_run, name="volume-indicator", daemon=True).start()
    try:
        _values.get_nowait()
    except queue.Empty:
        pass
    try:
        _values.put_nowait(item)
    except queue.Full:
        pass


def show_volume(value):
    """Solicita mostrar el último nivel sin bloquear el motor de atajos."""
    _post(("volume", max(0, min(100, round(value)))))


def show_message(icon, text, hint=""):
    """Aviso breve de modo: icono, nombre y (opcional) el atajo que lo activó."""
    _post(("message", GLYPHS.get(icon, GLYPHS["sliders-horizontal"]), str(text)[:24], str(hint)[:16]))


def _run():
    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        root.overrideredirect(True)
        root.configure(bg="#202124")
        root.attributes("-topmost", True)
        root.attributes("-toolwindow", True)
        root.geometry(f"{W}x{H}+0+0")
        canvas = tk.Canvas(root, width=W, height=H, bg="#202124", highlightthickness=0)
        canvas.pack()
        icon = canvas.create_text(22, 28, text="♪", fill="#f2f2f2", font=("Segoe UI", 17))
        track = canvas.create_line(48, 28, 225, 28, fill="#55585d", width=4, capstyle="round")
        level = canvas.create_line(48, 28, 48, 28, fill="#e5d18d", width=4, capstyle="round")
        label = canvas.create_text(254, 28, text="0", fill="white", font=("Segoe UI", 11, "bold"))
        title = canvas.create_text(52, 28, text="", fill="#f2f2f2", anchor="w", font=("Segoe UI", 13, "bold"), state="hidden")
        hint = canvas.create_text(W - 18, 28, text="", fill="#8b9099", anchor="e", font=("Segoe UI", 9), state="hidden")
        root.update_idletasks()
        user32 = ctypes.windll.user32
        hwnd = user32.GetParent(root.winfo_id()) or root.winfo_id()
        get_style = user32.GetWindowLongW
        set_style = user32.SetWindowLongW
        set_style(hwnd, -20, get_style(hwnd, -20) | 0x08000000 | 0x00000080)  # NOACTIVATE | TOOLWINDOW
        hide_timer = [None]
        latest = [None]

        def volume_view(on):
            for item in (track, level, label):
                canvas.itemconfigure(item, state="normal" if on else "hidden")
            for item in (title, hint):
                canvas.itemconfigure(item, state="hidden" if on else "normal")

        def render_notice(_event=None):
            item = latest[0]
            if item is not None:
                if item[0] == "volume":
                    volume_view(True)
                    canvas.itemconfigure(icon, text="♪", font=("Segoe UI", 17))
                    canvas.coords(level, 48, 28, 48 + 177 * item[1] / 100, 28)
                    canvas.itemconfigure(label, text=str(item[1]))
                else:
                    volume_view(False)
                    canvas.itemconfigure(icon, text=item[1], font=("Segoe MDL2 Assets", 18))
                    canvas.itemconfigure(title, text=item[2])
                    canvas.itemconfigure(hint, text=item[3])
                # Abajo a la derecha, sobre la bandeja, sin robar el foco a juegos ni editores.
                x, y = notice_origin(_work_area(user32, (0, 0, root.winfo_screenwidth(), root.winfo_screenheight())), W, H)
                user32.SetWindowPos(hwnd, -1, x, y, W, H, 0x0010 | 0x0040)  # NOACTIVATE | SHOWWINDOW
                if hide_timer[0] is not None:
                    root.after_cancel(hide_timer[0])
                hide_timer[0] = root.after(1800, hide_notice)

        def hide_notice():
            user32.ShowWindow(hwnd, 0)
            hide_timer[0] = None

        def dispatch():
            # Tk procesa el evento en su hilo; el motor solo escribe en la cola.
            while True:
                latest[0] = _values.get()
                try:
                    root.event_generate("<<DockerNotice>>", when="tail")
                except (RuntimeError, tk.TclError):
                    return

        root.bind("<<DockerNotice>>", render_notice)
        root.after(0, lambda: threading.Thread(target=dispatch, name="notice-dispatch", daemon=True).start())
        root.mainloop()
    except Exception:
        # El indicador es opcional: un fallo visual no debe romper el audio.
        pass
