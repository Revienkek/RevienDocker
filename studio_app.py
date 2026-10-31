"""
studio_app.py — RevienDocker como aplicación de escritorio (sin navegador).

  • Ventana propia sin marco de Windows (WebView2), con su barra de título y botones.
  • Icono en la bandeja: en modo Inteligente, cerrar la ventana la oculta y el motor sigue activo.
    En modo Directo no hace falta motor, así que cerrar sale del todo.
  • Una sola instancia (el puerto local actúa de cerrojo).
  • `--minimized` arranca directamente en la bandeja (para ponerlo en «Inicio» de Windows).

Se empaqueta con `build_exe.ps1` → dist/RevienDocker.exe
"""

import ctypes
import sys
import threading
import time

import pystray
import webview

import app
from app import ENGINE, PORT, make_server
from studio_icon import icon_image

TITLE = "RevienDocker"
MIN_W, MIN_H = 820, 560  # = min_size de la ventana
VK_LBUTTON = 0x01


class _Point(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


def main():
    try:
        server = make_server(PORT)
    except OSError:
        ctypes.windll.user32.MessageBoxW(0, "RevienDocker ya está en marcha: búscalo en la bandeja del sistema (junto al reloj).", TITLE, 0x40)
        return
    ENGINE.apply(ENGINE.studio, persist=False)  # reanuda el modo inteligente si estaba activo
    threading.Thread(target=server.serve_forever, daemon=True, name="studio-http").start()

    window = webview.create_window(TITLE, f"http://127.0.0.1:{PORT}/index.html", width=1040, height=720, min_size=(820, 560),
                                   frameless=True, easy_drag=False, background_color="#08090c", hidden="--minimized" in sys.argv)
    state = {"quit": False, "max": False}
    tray = None

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
            state["max"] = not state["max"]
        elif action == "close":
            if ENGINE.hook is not None and ENGINE.studio["mode"] == "smart":
                window.hide()  # el motor inteligente sigue en la bandeja
            else:
                quit_app()

    app.StudioHandler.window_control = control
    tray = pystray.Icon("revien-docker", icon_image(64), TITLE, menu=pystray.Menu(
        pystray.MenuItem("Abrir RevienDocker", lambda *_: window.show(), default=True),
        pystray.MenuItem("Salir", lambda *_: quit_app())))
    tray.run_detached()
    webview.start()
    tray.stop()
    ENGINE.stop()


if __name__ == "__main__":
    main()
