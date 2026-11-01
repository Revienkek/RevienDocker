"""Indicador discreto de volumen para los pasos exactos de RevienDocker."""

import ctypes
import queue
import threading

_values = queue.Queue(maxsize=1)
_lock = threading.Lock()
_started = False


def show_volume(value):
    """Solicita mostrar el último nivel sin bloquear el motor de atajos."""
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
        _values.put_nowait(max(0, min(100, round(value))))
    except queue.Full:
        pass


def _run():
    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        root.overrideredirect(True)
        root.configure(bg="#202124")
        root.attributes("-topmost", True)
        root.attributes("-toolwindow", True)
        root.geometry("280x56+0+0")
        canvas = tk.Canvas(root, width=280, height=56, bg="#202124", highlightthickness=0)
        canvas.pack()
        canvas.create_text(22, 28, text="♪", fill="#f2f2f2", font=("Segoe UI", 17))
        canvas.create_line(48, 28, 225, 28, fill="#55585d", width=4, capstyle="round")
        level = canvas.create_line(48, 28, 48, 28, fill="#e5d18d", width=4, capstyle="round")
        label = canvas.create_text(254, 28, text="0", fill="white", font=("Segoe UI", 11, "bold"))
        root.update_idletasks()
        user32 = ctypes.windll.user32
        hwnd = user32.GetParent(root.winfo_id()) or root.winfo_id()
        get_style = user32.GetWindowLongW
        set_style = user32.SetWindowLongW
        set_style(hwnd, -20, get_style(hwnd, -20) | 0x08000000 | 0x00000080)  # NOACTIVATE | TOOLWINDOW
        until = [0.0]

        def poll():
            import time
            try:
                value = _values.get_nowait()
            except queue.Empty:
                value = None
            if value is not None:
                canvas.coords(level, 48, 28, 48 + 177 * value / 100, 28)
                canvas.itemconfigure(label, text=str(value))
                # Posición cercana a la barra, sin robar el foco a juegos ni editores.
                x = max(16, int(root.winfo_screenwidth() * 0.075))
                y = max(16, root.winfo_screenheight() - 150)
                user32.SetWindowPos(hwnd, -1, x, y, 280, 56, 0x0010 | 0x0040)  # NOACTIVATE | SHOWWINDOW
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
