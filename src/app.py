"""
app.py — RevienDocker · backend & CH57x USB-HID Flasher (Vía 2B)
Soporta flasheo directo por USB HID (0x1189:0x8890 / 0x8840) y Modo Simulador
automático para trabajar en la interfaz antes de conectar el hardware físico.
"""

import json
from functools import wraps
from mode_light import ModeLight
import sys
import threading
import time
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler, ThreadingHTTPServer

from studio_engine import ENGINE, RESOURCE_DIR, list_windows

# Intentamos cargar hidapi; si no está instalado o no hay hardware, usamos Simulador
try:
    import hid
    HID_AVAILABLE = True
except ImportError:
    HID_AVAILABLE = False

VENDOR_ID = 0x1189
PRODUCT_IDS = [0x8890, 0x8840]
VENDOR_USAGE_PAGE = 0xFF00
REPORT_ID = 0x03

SLOTS = {
    "KEY_1": 0x01,
    "KEY_2": 0x02,
    "KEY_3": 0x03,
    "KNOB_CCW": 0x0D,
    "KNOB_PRESS": 0x0E,
    "KNOB_CW": 0x0F,
}


USB_LOCK = threading.RLock()


def usb_serialized(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        with USB_LOCK:
            return fn(*args, **kwargs)
    return wrapped


class CH57xController:
    """Controlador directo de bajo nivel para la EEPROM de teclados WCH CH57x."""

    def __init__(self):
        self.device = None
        self.simulated = True

    def connect(self) -> dict:
        if not HID_AVAILABLE:
            self.simulated = True
            return {"connected": False, "mode": "SIMULATOR (librería hidapi no instalada)"}

        for pid in PRODUCT_IDS:
            devices = hid.enumerate(VENDOR_ID, pid)
            for d in devices:
                if d.get("usage_page") == VENDOR_USAGE_PAGE or d.get("interface_number") == 1:
                    try:
                        dev = hid.device()
                        dev.open_path(d["path"])
                        self.device = dev
                        self.simulated = False
                        return {
                            "connected": True,
                            "mode": "HARDWARE_USB",
                            "vid": hex(VENDOR_ID),
                            "pid": hex(pid),
                            "path": str(d["path"]),
                        }
                    except Exception as exc:
                        return {"connected": False, "mode": f"ERROR_OPEN: {exc}"}

        self.simulated = True
        return {"connected": False, "mode": "SIMULATOR (Hardware 0x1189:0x8890 no detectado)"}

    def probe(self) -> dict:
        """¿Hay un macropad conectado? Solo enumera: no abre el dispositivo."""
        if not HID_AVAILABLE:
            return {"connected": False, "reason": "hidapi no disponible"}
        for pid in PRODUCT_IDS:
            for d in hid.enumerate(VENDOR_ID, pid):
                if d.get("usage_page") == VENDOR_USAGE_PAGE or d.get("interface_number") == 1:
                    return {"connected": True, "name": d.get("product_string") or "Macropad CH57x", "pid": hex(pid)}
        return {"connected": False, "reason": "no detectado"}

    @staticmethod
    def key_messages(slot_name: str, action_type: str, modifiers: int, code: int, wheel: int = 0, speed: int = 1) -> list:
        """Mensajes que fijan UN botón (capa 1). Protocolo del CH57x 0x8890, el mismo de ch57x-keyboard-tool:
        inicio `03 FE capa 01 01`, uno o varios mensajes del botón y cierre `03 AA AA`.
        Cada mensaje son 64 bytes: el primero es el Report ID 0x03."""
        sid = SLOTS.get(slot_name, 0x01)
        layer = 0x10  # (capa 0 + 1) << 4
        def msg(*b):
            m = bytearray(64)
            m[0] = REPORT_ID
            m[1:1 + len(b)] = bytes(x & 0xFF for x in b)
            return bytes(m)
        out = [msg(0xFE, 0x01, 0x01, 0x01)]
        if action_type == "media":
            out.append(msg(sid, layer | 0x02, code & 0xFF, (code >> 8) & 0xFF))
        elif action_type == "mouse":
            # botones, dx, dy, rueda con signo, modificadores (la velocidad multiplica la rueda)
            out.append(msg(sid, layer | 0x03, code, 0, 0, wheel * max(1, speed), modifiers))
        else:
            out.append(msg(sid, layer | 0x01, 1, 0, 0, 0))                    # el firmware pide primero una tecla vacía
            out.append(msg(sid, layer | 0x01, 1, 1, modifiers, code))         # largo 1, posición 1, modificadores, tecla
        out.append(msg(0xAA, 0xAA))
        return out

    @classmethod
    def flash_messages(cls, mappings: dict, led_mode: int = 1) -> list:
        """Secuencia completa como lista de (etiqueta, mensaje de 64 bytes)."""
        seq = []
        for slot_name, cfg in mappings.items():
            msgs = cls.key_messages(slot_name, cfg.get("type", "keyboard"), int(cfg.get("modifiers", 0)),
                                    int(cfg.get("hid_code", 0)), int(cfg.get("wheel", 0)), int(cfg.get("speed", 1)))
            seq += [(f"{slot_name}", m) for m in msgs]
        return seq + cls.led_messages(led_mode)

    @staticmethod
    def led_messages(mode: int) -> list:
        """Luz del teclado: `A1 01`, `B0 18 <modo>`, `AA A1`. Solo se conocen los modos 0, 1 y 2; el color no se programa."""
        return [("LED", bytes([REPORT_ID, 0xA1, 0x01]) + bytes(61)),
                ("LED", bytes([REPORT_ID, 0xB0, 0x18, mode & 0xFF]) + bytes(60)),
                ("LED", bytes([REPORT_ID, 0xAA, 0xA1]) + bytes(61))]

    @usb_serialized
    def set_led(self, mode: int) -> dict:
        """Cambia solo la luz, al instante. `sent` es False si no hay teclado (simulador)."""
        status = self.connect()
        logs = []
        try:
            for tag, m in self.led_messages(mode):
                self._send(m, logs, tag)
        finally:
            if self.device:
                self.device.close()
                self.device = None
        return {"sent": bool(status.get("connected")), "logs": logs}

    @usb_serialized
    def flash_mappings(self, mappings: dict, led_mode: int = 1) -> list:
        """Escribe todos los botones y la luz. Lanza OSError si el teclado rechaza algún mensaje."""
        status = self.connect()
        logs = [f"Estado del bus: {status['mode']}"]
        try:
            for tag, m in self.flash_messages(mappings, led_mode):
                self._send(m, logs, tag)
        finally:
            if self.device:
                self.device.close()
                self.device = None
        return logs

    def _send(self, pkt: bytes, logs: list, tag: str):
        hex_preview = " ".join(f"{b:02X}" for b in pkt[:10])
        if not self.simulated and self.device:
            n = self.device.write(pkt)
            if n < 0:
                raise OSError(f"el teclado rechazó el mensaje {tag}: {self.device.error()}")
            logs.append(f"[TX USB] {tag}: {hex_preview} ...")
            time.sleep(0.01)
        else:
            logs.append(f"[SIMULADOR] {tag}: {hex_preview} ...")


MODE_LIGHT = ModeLight(CH57xController().set_led, lambda: ENGINE.studio["led_mode"], USB_LOCK)
ENGINE.mode_light = MODE_LIGHT

BASE_DIR = RESOURCE_DIR
PORT = 8765
# Acciones permitidas en /api/window (las resuelve studio_app.py; cualquier otra se rechaza).
WINDOW_ACTIONS = ("minimize", "maximize", "close", "show", "restore",
                  "resize-n", "resize-s", "resize-e", "resize-w",
                  "resize-ne", "resize-nw", "resize-se", "resize-sw")


class StudioHandler(SimpleHTTPRequestHandler):
    """Sirve index.html y los estáticos desde la carpeta del proyecto y expone /api/flash."""

    controller = CH57xController()

    engine = ENGINE
    window_control = None  # lo fija studio_app.py: callable(acción) para minimizar / maximizar / cerrar la ventana propia

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def log_message(self, fmt, *args):  # sin consola (.exe) no hay stderr; /api/status se consulta cada 1,5 s
        if sys.stderr is not None and "/api/status" not in (args[0] if args else ""):
            super().log_message(fmt, *args)

    def _json(self, obj, code=200):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _api_allowed(self) -> bool:
        """Una web externa no debe poder pulsar teclas en tu PC: solo Host local y cabecera propia
        (esa cabecera obliga al navegador a pedir permiso CORS, que nunca concedemos)."""
        host = (self.headers.get("Host") or "").split(":")[0]
        if host not in ("127.0.0.1", "localhost"):
            return False
        return self.command == "GET" or self.headers.get("X-Studio") == "1"

    def do_GET(self):
        if not self.path.startswith("/api/"):
            return super().do_GET()
        if not self._api_allowed():
            return self._json({"ok": False, "error": "forbidden"}, 403)
        if self.path == "/api/status":
            return self._json({"ok": True, **self.engine.status(), "desktop": self.window_control is not None})
        if self.path == "/api/config":
            return self._json({"ok": True, "studio": self.engine.studio})
        if self.path.startswith("/api/record"):
            since = int(self.path.partition("since=")[2] or 0)
            return self._json({"ok": True, **self.engine.capture_events(since)})
        if self.path == "/api/device":
            return self._json({"ok": True, **self.controller.probe()})
        if self.path == "/api/windows":
            return self._json({"ok": True, "windows": list_windows()})
        self._json({"ok": False, "error": "not found"}, 404)

    def do_POST(self):
        if not self.path.startswith("/api/"):
            return self.send_error(404)
        if not self._api_allowed():
            return self._json({"ok": False, "error": "forbidden"}, 403)
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length > 1_000_000:
                return self._json({"ok": False, "error": "too large"}, 413)
            body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except ValueError:
            return self._json({"ok": False, "error": "bad json"}, 400)
        if self.path == "/api/flash":
            try:
                with USB_LOCK:
                    MODE_LIGHT.cancel()
                    logs = self.controller.flash_mappings(body.get("mappings", {}), led_mode=int(body.get("led_mode", 1)))
            except OSError as exc:
                return self._json({"ok": False, "error": str(exc)})
            return self._json({"ok": True, "logs": logs})
        if self.path == "/api/led":
            try:
                with USB_LOCK:
                    MODE_LIGHT.cancel()
                    res = self.controller.set_led(max(0, min(255, int(body.get("mode", 1)))))
            except (OSError, ValueError) as exc:
                return self._json({"ok": False, "error": str(exc)})
            return self._json({"ok": True, **res})
        if self.path == "/api/config":
            studio = self.engine.apply(body.get("studio", {}))
            return self._json({"ok": True, "studio": studio, **self.engine.status(), "desktop": self.window_control is not None})
        if self.path == "/api/window":
            if self.window_control is None or body.get("action") not in WINDOW_ACTIONS:
                return self._json({"ok": False}, 400)
            # Leer desde la clase evita convertir la función en método. El arrastre
            # ya inicia su propio hilo; las demás acciones pueden informar errores.
            try:
                type(self).window_control(body["action"])
            except Exception as exc:
                return self._json({"ok": False, "error": str(exc)}, 500)
            return self._json({"ok": True})
        if self.path == "/api/record":
            if body.get("action") == "start":
                return self._json({"ok": self.engine.start_capture()})
            self.engine.stop_capture()
            return self._json({"ok": True})
        if self.path == "/api/mode":
            try:
                self.engine.set_mode(int(body.get("slot", -1)))
            except (TypeError, ValueError):
                return self._json({"ok": False, "error": "bad slot"}, 400)
            return self._json({"ok": True, **self.engine.status()})
        if self.path == "/api/run":
            ok = self.engine.run_now(body.get("action", {}), min(10.0, float(body.get("delay", 0))))
            return self._json({"ok": ok})
        self._json({"ok": False, "error": "not found"}, 404)


class SingleInstanceServer(ThreadingHTTPServer):
    allow_reuse_address = False


def make_server(port: int = PORT) -> ThreadingHTTPServer:
    """Crea el servidor local (solo 127.0.0.1). Lanza OSError si el puerto está ocupado (otra instancia)."""
    return SingleInstanceServer(("127.0.0.1", port), StudioHandler)


def serve(port: int = PORT, open_browser: bool = False):
    """Modo desarrollo: servidor + navegador. La app de escritorio (studio_app.py) no usa esto."""
    url = f"http://127.0.0.1:{port}/index.html"
    print("=" * 60)
    print(f" REVIENDOCKER ACTIVO EN: {url}")
    print("=" * 60)
    if open_browser:
        import webbrowser
        webbrowser.open(url)
    ENGINE.apply(ENGINE.studio, persist=False)  # el motor arranca siempre: el docker y la app son uno
    make_server(port).serve_forever()


if __name__ == "__main__":
    serve()
