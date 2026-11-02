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
from version import __version__

TITLE = "RevienDocker"
# Ventana de tamaño fijo (PRODUCT.md): no se redimensiona ni se maximiza.
WIN_W, WIN_H = 720, 420
MUTEX_NAME = "Local\\RevienDocker_SingleInstance_Mutex"
ERROR_ALREADY_EXISTS = 183


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

    window = webview.create_window(TITLE, f"http://127.0.0.1:{PORT}/index.html", width=WIN_W, height=WIN_H, resizable=False,
                                   frameless=True, easy_drag=False, background_color="#08090c", hidden="--minimized" in sys.argv)
    state = {"quit": False, "hidden": "--minimized" in sys.argv, "minimized": False}
    tray = None

    def set_restored():
        state["minimized"] = False
        if tray:
            tray.update_menu()

    def set_minimized():
        state["minimized"] = True
        if tray:
            tray.update_menu()

    window.events.restored += set_restored

    def fit_client():
        """Windows resta el marco al crear la ventana sin marco: se mide el área real de la página y se corrige
        hasta que sea exactamente WIN_W × WIN_H (la interfaz está maquetada a ese tamaño)."""
        for _ in range(3):
            try:
                w, h = window.evaluate_js("[window.innerWidth, window.innerHeight]")
            except Exception:
                return
            dw, dh = WIN_W - int(w), WIN_H - int(h)
            if not dw and not dh:
                return
            window.resize(window.width + dw, window.height + dh)

    def no_maximize():
        """Sin botón de maximizar: tampoco por Win+Flecha arriba ni al arrastrar la ventana a un borde."""
        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW(None, TITLE)
        if hwnd:
            user32.SetWindowLongW(hwnd, -16, user32.GetWindowLongW(hwnd, -16) & ~0x10000)  # GWL_STYLE, WS_MAXIMIZEBOX

    window.events.loaded += fit_client
    window.events.loaded += no_maximize
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

    def quit_app():
        state["quit"] = True
        if tray:
            tray.stop()
        ENGINE.stop()
        window.destroy()

    def control(action):
        if action == "minimize":
            window.minimize()
        elif action == "close":
            if ENGINE.hook is not None:
                hide_to_tray()  # el motor inteligente sigue en la bandeja
            else:
                quit_app()
        elif action in ("show", "restore"):
            show_window()

    app.StudioHandler.window_control = control
    tray = pystray.Icon("revien-docker", icon_image(64), f"{TITLE} {__version__}", menu=pystray.Menu(
        pystray.MenuItem(lambda _: "Mostrar RevienDocker" if state["hidden"] or state["minimized"] else "Minimizar a la bandeja",
                         lambda *_: toggle_window(), default=True),
        pystray.MenuItem("Salir", lambda *_: quit_app())))
    tray.run_detached()
    webview.start()
    tray.stop()
    ENGINE.stop()


if __name__ == "__main__":
    main()
