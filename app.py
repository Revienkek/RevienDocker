"""
app.py — RevienDocker · backend & CH57x USB-HID Flasher (Vía 2B)
Soporta flasheo directo por USB HID (0x1189:0x8890 / 0x8840) y Modo Simulador
automático para trabajar en la interfaz antes de conectar el hardware físico.
"""

import json
import sys
import threading
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
    def build_packet(slot_name: str, action_type: str, modifiers: int, hid_code: int,
                     wheel: int = 0, speed: int = 1) -> bytes:
        """Construye la trama exacta de 65 bytes (Report ID 0x03 + 64B payload)."""
        slot_id = SLOTS.get(slot_name, 0x01)
        pkt = bytearray(65)
        pkt[0] = REPORT_ID
        pkt[1] = slot_id

        if action_type == "keyboard":
            pkt[2] = 0x11  # Layer 1 + Tipo Teclado (1)
            pkt[3] = 0x01  # Longitud de macro: 1 tecla
            pkt[4] = 0x01  # Secuencia índice 1
            pkt[5] = modifiers & 0xFF
            pkt[6] = hid_code & 0xFF
        elif action_type == "media":
            pkt[2] = 0x12  # Layer 1 + Tipo Multimedia (2)
            pkt[3] = hid_code & 0xFF
            pkt[4] = (hid_code >> 8) & 0xFF
            pkt[5] = max(1, speed) & 0xFF  # repeticiones por paso (velocidad de la rueda)
        elif action_type == "mouse":
            pkt[2] = 0x13  # Layer 1 + Tipo Ratón (3)
            pkt[3] = modifiers & 0xFF      # modificadores (ej. Ctrl + rueda = zoom)
            pkt[4] = hid_code & 0xFF       # máscara de botones: 1 izq, 2 der, 4 central, 8 atrás, 16 adelante
            pkt[5] = (wheel * max(1, speed)) & 0xFF  # rueda con signo: +arriba / -abajo

        return bytes(pkt)

    def flash_mappings(self, mappings: dict, led_mode: int = 1) -> list:
        """Envía la secuencia completa Unlock -> Slots -> Commit a la EEPROM."""
        status = self.connect()
        logs = [f"Estado del bus: {status['mode']}"]

        unlock_pkt = bytearray(65)
        unlock_pkt[0] = REPORT_ID
        unlock_pkt[1] = 0xA1
        unlock_pkt[2] = 0x01
        self._send(unlock_pkt, logs, "UNLOCK_EEPROM")

        for slot_name, cfg in mappings.items():
            pkt = self.build_packet(
                slot_name=slot_name,
                action_type=cfg.get("type", "keyboard"),
                modifiers=int(cfg.get("modifiers", 0)),
                hid_code=int(cfg.get("hid_code", 104)),
                wheel=int(cfg.get("wheel", 0)),
                speed=int(cfg.get("speed", 1)),
            )
            self._send(pkt, logs, f"WRITE_{slot_name}")

        led_pkt = bytearray(65)
        led_pkt[0] = REPORT_ID
        led_pkt[1] = 0xA2
        led_pkt[2] = led_mode & 0xFF
        self._send(led_pkt, logs, "SET_LED")

        commit_pkt = bytearray(65)
        commit_pkt[0] = REPORT_ID
        commit_pkt[1] = 0xAA
        commit_pkt[2] = 0xAA
        self._send(commit_pkt, logs, "COMMIT_EEPROM")

        if self.device:
            self.device.close()
            self.device = None

        return logs

    def _send(self, pkt: bytes, logs: list, tag: str):
        hex_preview = " ".join(f"{b:02X}" for b in pkt[:12])
        if not self.simulated and self.device:
            self.device.write(pkt)
            logs.append(f"[TX USB] {tag}: {hex_preview} ...")
        else:
            logs.append(f"[SIMULADOR] {tag}: {hex_preview} ...")


BASE_DIR = RESOURCE_DIR
PORT = 8765
# Acciones permitidas en /api/window (las resuelve studio_app.py; cualquier otra se rechaza).
WINDOW_ACTIONS = ("minimize", "maximize", "close",
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
            logs = self.controller.flash_mappings(body.get("mappings", {}), led_mode=int(body.get("led_mode", 1)))
            return self._json({"ok": True, "logs": logs})
        if self.path == "/api/config":
            studio = self.engine.apply(body.get("studio", {}))
            return self._json({"ok": True, "studio": studio, **self.engine.status(), "desktop": self.window_control is not None})
        if self.path == "/api/window":
            if self.window_control is None or body.get("action") not in WINDOW_ACTIONS:
                return self._json({"ok": False}, 400)
            # type(self): leer la función desde la clase evita que Python la convierta en método
            threading.Thread(target=type(self).window_control, args=(body["action"],), daemon=True).start()
            return self._json({"ok": True})
        if self.path == "/api/record":
            if body.get("action") == "start":
                return self._json({"ok": self.engine.start_capture()})
            self.engine.stop_capture()
            return self._json({"ok": True})
        if self.path == "/api/run":
            ok = self.engine.run_now(body.get("action", {}), min(10.0, float(body.get("delay", 0))))
            return self._json({"ok": ok})
        self._json({"ok": False, "error": "not found"}, 404)


def make_server(port: int = PORT) -> ThreadingHTTPServer:
    """Crea el servidor local (solo 127.0.0.1). Lanza OSError si el puerto está ocupado (otra instancia)."""
    return ThreadingHTTPServer(("127.0.0.1", port), StudioHandler)


def serve(port: int = PORT, open_browser: bool = False):
    """Modo desarrollo: servidor + navegador. La app de escritorio (studio_app.py) no usa esto."""
    url = f"http://127.0.0.1:{port}/index.html"
    print("=" * 60)
    print(f" REVIENDOCKER ACTIVO EN: {url}")
    print("=" * 60)
    if open_browser:
        import webbrowser
        webbrowser.open(url)
    ENGINE.apply(ENGINE.studio, persist=False)  # arranca el motor si lo guardado está en modo inteligente
    make_server(port).serve_forever()


if __name__ == "__main__":
    serve()
