"""
studio_app.py — RevienDocker como aplicación de escritorio (sin navegador).

  • Ventana propia sin marco de Windows (WebView2), con su barra de título y botones.
  • Vive en la bandeja del sistema, sin botón en la barra de tareas: minimizar la oculta ahí y cerrarla también
    (el motor sigue activo, el docker lo necesita). Solo «Salir» de la bandeja cierra del todo.
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
WIN_W, WIN_H = 720, 348
CORNER_MARGIN = 12   # px entre la ventana y los bordes del área útil al abrir
OFFSCREEN = -32000   # la ventana nace fuera de pantalla y solo se muestra ya colocada: sin parpadeo en otra esquina
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

    webview.settings["DRAG_REGION_DIRECT_TARGET_ONLY"] = True   # arrastra solo desde el propio elemento marcado (ver studio.js)
    window = webview.create_window(TITLE, f"http://127.0.0.1:{PORT}/index.html", width=WIN_W, height=WIN_H, x=OFFSCREEN, y=OFFSCREEN,
                                   resizable=False, frameless=True, easy_drag=False, background_color="#08090c", hidden="--minimized" in sys.argv)
    state = {"quit": False, "hidden": "--minimized" in sys.argv, "minimized": False}
    tray = None

    def notify_visibility(visible):
        try:
            window.evaluate_js(f"window.setDesktopVisible && window.setDesktopVisible({str(visible).lower()})")
        except Exception:
            pass  # el documento puede estar cargando o cerrándose

    def set_restored():
        state["minimized"] = False
        notify_visibility(not state["hidden"])
        if tray:
            tray.update_menu()

    def set_minimized():
        state["minimized"] = True   # Win+Abajo, «Mostrar escritorio»…: sin botón en la barra de tareas, también va a la bandeja
        hide_to_tray()

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

    class RECT(ctypes.Structure):
        _fields_ = [(n, ctypes.c_long) for n in ("left", "top", "right", "bottom")]

    placed = []

    def place_corner(force=False):
        """Esquina inferior derecha del área útil del monitor principal (justo sobre la barra de tareas). Se coloca sola al abrir
        (la ventana nace fuera de pantalla y esta es la primera vez que se ve) y, con force, cuando el usuario la pide."""
        if placed and not force:
            return
        placed.append(True)
        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW(None, TITLE)
        if not hwnd:
            return
        rect, work = RECT(), RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        if not user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(work), 0):  # SPI_GETWORKAREA
            return
        x = work.right - (rect.right - rect.left) - CORNER_MARGIN
        y = work.bottom - (rect.bottom - rect.top) - CORNER_MARGIN
        user32.SetWindowPos(hwnd, 0, x, y, 0, 0, 0x0001 | 0x0004 | 0x0010)  # sin cambiar tamaño, orden ni foco

    def tray_only():
        """Sin botón en la barra de tareas ni en Alt+Tab (ventana de herramientas): la app solo se ve en la bandeja."""
        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW(None, TITLE)
        if not hwnd:
            return
        ex = user32.GetWindowLongW(hwnd, -20)  # GWL_EXSTYLE
        new = (ex | 0x80) & ~0x40000           # WS_EX_TOOLWINDOW sí, WS_EX_APPWINDOW no
        if new == ex:
            return
        visible = user32.IsWindowVisible(hwnd)
        if visible:
            user32.ShowWindow(hwnd, 0)         # SW_HIDE: el cambio solo se aplica con la ventana oculta
        user32.SetWindowLongW(hwnd, -20, new)
        if visible:
            user32.ShowWindow(hwnd, 4)         # SW_SHOWNOACTIVATE

    def on_loaded():
        notify_visibility(not state["hidden"] and not state["minimized"])
        fit_client()   # redimensionar muestra la ventana (SWP_SHOWWINDOW): si arranca en la bandeja, se vuelve a ocultar ya
        if state["hidden"]:
            window.hide()
        no_maximize()
        tray_only()
        place_corner()

    window.events.loaded += on_loaded
    window.events.minimized += set_minimized

    def hide_to_tray():
        notify_visibility(False)
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
        notify_visibility(True)
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
            hide_to_tray()  # minimizar es ir a la bandeja: no hay botón en la barra de tareas
        elif action == "close":
            if ENGINE.hook is not None:
                hide_to_tray()  # el motor inteligente sigue en la bandeja
            else:
                quit_app()
        elif action in ("show", "restore"):
            show_window()
        elif action == "corner":
            place_corner(force=True)  # clic derecho en una zona de arrastre: vuelve a su sitio de siempre

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
