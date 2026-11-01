"""
studio_app.py — RevienDocker como aplicación de escritorio (sin navegador).

  • Ventana propia sin marco de Windows (WebView2), con su barra de título y botones.
  • Icono en la bandeja: cerrar la ventana la oculta y el motor sigue activo (el docker lo necesita).
    Solo «Salir» de la bandeja cierra del todo.
  • Una sola instancia (el puerto local actúa de cerrojo).
  • `--minimized` arranca directamente en la bandeja (para ponerlo en «Inicio» de Windows).

Se empaqueta con `build_exe.ps1` → dist/RevienDocker.exe
"""

import ctypes
import os
import sys
import threading
import time

# Declarar Per-Monitor V2 DPI awareness antes de inicializar ningún control WinForms / WebView2
try:
    ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
except Exception:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass

import pystray
import webview

import app
from app import ENGINE, PORT, make_server
from studio_icon import icon_image

TITLE = "RevienDocker"
MIN_W, MIN_H = 720, 560  # = min_size de la ventana
VK_LBUTTON = 0x01
MUTEX_NAME = "Local\\RevienDocker_SingleInstance_Mutex"
ERROR_ALREADY_EXISTS = 183


class _Point(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


def activate_existing_instance() -> bool:
    """Intenta despertar la instancia ya abierta por HTTP y traerla al frente."""
    try:
        import urllib.request
        req = urllib.request.Request(
            f"http://127.0.0.1:{PORT}/api/window",
            data=b'{"action":"show"}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            return resp.status == 200
    except Exception:
        pass
    user32 = ctypes.windll.user32
    hwnd = user32.FindWindowW(None, TITLE)
    if hwnd:
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        user32.SetForegroundWindow(hwnd)
        return True
    return False


def main():
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if ctypes.windll.kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
        activate_existing_instance()
        return

    try:
        server = make_server(PORT)
    except OSError:
        if not activate_existing_instance():
            ctypes.windll.user32.MessageBoxW(0, "RevienDocker ya está en marcha: búscalo en la bandeja del sistema (junto al reloj).", TITLE, 0x40)
        return
    ENGINE.apply(ENGINE.studio, persist=False)  # el motor arranca siempre: el docker y la app son uno
    threading.Thread(target=server.serve_forever, daemon=True, name="studio-http").start()

    window = webview.create_window(TITLE, f"http://127.0.0.1:{PORT}/index.html", width=760, height=720, min_size=(MIN_W, MIN_H),
                                   frameless=True, easy_drag=False, background_color="#08090c", hidden="--minimized" in sys.argv)
    state = {"quit": False, "max": False, "hidden": "--minimized" in sys.argv, "minimized": False}
    tray = None

    def set_maximized():
        state["max"] = True

    def set_restored():
        state["max"] = False
        state["minimized"] = False
        if tray:
            tray.update_menu()

    def set_minimized():
        state["minimized"] = True
        if tray:
            tray.update_menu()

    window.events.maximized += set_maximized
    window.events.restored += set_restored
    window.events.minimized += set_minimized

    def hide_to_tray():
        window.hide()
        state["hidden"] = True
        if tray:
            tray.update_menu()

    def show_window():
        window.show()
        if state["minimized"]:
            window.restore()
        state["hidden"] = False
        state["minimized"] = False
        if tray:
            tray.update_menu()
        hwnd = ctypes.windll.user32.FindWindowW(None, TITLE)
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            ctypes.windll.user32.SetForegroundWindow(hwnd)

    def toggle_window():
        if state["hidden"] or state["minimized"]:
            show_window()
        else:
            hide_to_tray()

    def resize_drag(edge):
        """Ventana sin marco: Windows no ofrece borde nativo que arrastrar, así que seguimos el ratón
        mientras el botón siga pulsado y ajustamos tamaño y posición (mínimo = min_size)."""
        if state["max"]:
            return
        user32 = ctypes.windll.user32
        scale = (user32.GetDpiForWindow(user32.FindWindowW(None, TITLE)) or 96) / 96

        def run():
            start = _Point()
            user32.GetCursorPos(ctypes.byref(start))
            x0, y0, w0, h0 = window.x, window.y, window.width, window.height
            while user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000:
                now = _Point()
                user32.GetCursorPos(ctypes.byref(now))
                dx, dy = (now.x - start.x) / scale, (now.y - start.y) / scale
                x, y, w, h = x0, y0, w0, h0
                if "w" in edge:
                    w = max(MIN_W, w0 - dx)
                    x = x0 + w0 - w
                if "e" in edge:
                    w = max(MIN_W, w0 + dx)
                if "n" in edge:
                    h = max(MIN_H, h0 - dy)
                    y = y0 + h0 - h
                if "s" in edge:
                    h = max(MIN_H, h0 + dy)
                window.resize(round(w), round(h))
                window.move(round(x), round(y))
                time.sleep(0.01)

        threading.Thread(target=run, daemon=True, name="studio-resize").start()

    def quit_app():
        state["quit"] = True
        if tray:
            tray.stop()
        ENGINE.stop()
        window.destroy()

    def control(action):
        if action.startswith("resize-"):
            resize_drag(action[len("resize-"):])
        elif action == "minimize":
            window.minimize()
        elif action == "maximize":
            window.restore() if state["max"] else window.maximize()
        elif action == "close":
            if ENGINE.hook is not None:
                hide_to_tray()  # el motor inteligente sigue en la bandeja
            else:
                quit_app()
        elif action in ("show", "restore"):
            show_window()

    app.StudioHandler.window_control = control
    tray = pystray.Icon("revien-docker", icon_image(64), TITLE, menu=pystray.Menu(
        pystray.MenuItem(lambda _: "Mostrar RevienDocker" if state["hidden"] or state["minimized"] else "Minimizar a la bandeja",
                         lambda *_: toggle_window(), default=True),
        pystray.MenuItem("Salir", lambda *_: quit_app())))
    tray.run_detached()
    webview.start()
    tray.stop()
    ENGINE.stop()


if __name__ == "__main__":
    main()
