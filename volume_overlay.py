"""Indicador discreto sobre la barra de tareas: nivel de volumen y cambio de modo (icono + poco texto)."""

import ctypes
import queue
import threading

_values = queue.Queue(maxsize=1)
_lock = threading.Lock()
_started = False

# Iconos de «Segoe MDL2 Assets» (incluida en Windows) para los iconos que ofrece la interfaz.
GLYPHS = {"target": "\uE765", "music": "\uE8D6", "mic": "\uE720", "clapperboard": "\uE714", "app-window": "\uE774",
          "brush": "\uE790", "code-xml": "\uE943", "gamepad-2": "\uE7FC", "pen-line": "\uE70F", "sliders-horizontal": "\uE713"}
W, H = 280, 56


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
        until = [0.0]

        def volume_view(on):
            for item in (track, level, label):
                canvas.itemconfigure(item, state="normal" if on else "hidden")
            for item in (title, hint):
                canvas.itemconfigure(item, state="hidden" if on else "normal")

        def poll():
            import time
            try:
                item = _values.get_nowait()
            except queue.Empty:
                item = None
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
                # Posición cercana a la barra, sin robar el foco a juegos ni editores.
                x = max(16, int(root.winfo_screenwidth() * 0.075))
                y = max(16, root.winfo_screenheight() - 150)
                user32.SetWindowPos(hwnd, -1, x, y, W, H, 0x0010 | 0x0040)  # NOACTIVATE | SHOWWINDOW
                until[0] = time.monotonic() + 1.8
            elif until[0] and time.monotonic() >= until[0]:
                user32.ShowWindow(hwnd, 0)
                until[0] = 0.0
            root.after(40, poll)

        root.after(40, poll)
        root.mainloop()
    except Exception:
        # El indicador es opcional: un fallo visual no debe romper el audio.
        pass
