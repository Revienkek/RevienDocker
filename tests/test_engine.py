"""Pruebas del motor inteligente, sin hardware y sin OBS real: `python -m unittest discover -s tests -t . -v`"""

import base64
import hashlib
import json
import os
import socket
import struct
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import app
import studio_engine as se

K = lambda mod, code: {"type": "keyboard", "mod": mod, "code": code, "wheel": 0, "speed": 1}
OBS_NEXT = {"type": "obs", "mod": 0, "code": 0, "wheel": 0, "speed": 1, "op": "next_scene", "target": ""}

STUDIO = {
    "mode": "smart", "trigger": "shift",
    "layers": [
        {"id": "base", "name": "Base", "actions": {"KEY_1": K(1, 0x06), "KEY_2": K(0, 0x28)}},
        {"id": "obs", "name": "OBS", "exes": ["OBS64.exe"], "actions": {"KEY_1": OBS_NEXT}},
    ],
}


class ResolveTests(unittest.TestCase):
    def setUp(self):
        self.s = se.normalize_studio(STUDIO)

    def test_sin_tecla_de_activacion_usa_base(self):
        self.assertEqual(se.resolve(self.s, "KEY_1", "obs64.exe", False)[1], "base")

    def test_con_activacion_usa_capa_de_la_app(self):
        a, layer = se.resolve(self.s, "KEY_1", "obs64.exe", True)
        self.assertEqual((layer, a["op"]), ("obs", "next_scene"))

    def test_boton_sin_accion_en_la_capa_cae_a_base(self):
        a, layer = se.resolve(self.s, "KEY_2", "obs64.exe", True)
        self.assertEqual(layer, "base")
        self.assertEqual(a["code"], 0x28)

    def test_app_sin_capa_cae_a_base(self):
        self.assertEqual(se.resolve(self.s, "KEY_1", "notepad.exe", True)[1], "base")

    def test_normalize_descarta_basura(self):
        s = se.normalize_studio({"mode": "x", "trigger": "win", "layers": [
            {"id": "../evil", "actions": {"KEY_1": {"type": "obs", "op": "format_c"}, "NOPE": K(0, 4)}}]})
        self.assertEqual((s["mode"], s["trigger"], s["layers"][0]["id"]), ("direct", "shift", "base"))
        self.assertEqual(s["layers"][1]["id"], "evil")
        self.assertEqual(s["layers"][1]["actions"], {})

    def test_guardar_y_cargar(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "studio.json"
            se.save_studio(STUDIO, p)
            self.assertEqual(se.load_studio(p)["layers"][1]["exes"], ["obs64.exe"])


MODOS = [{"name": "Música", "icon": "music", "actions": {"KEY_1": K(0, 0x05), "KNOB_CW": K(0, 0x06)}}, None, None]


class ModeTests(unittest.TestCase):
    def setUp(self):
        self.s = se.normalize_studio({**STUDIO, "modes": MODOS})

    def test_normalize_siempre_tres_huecos(self):
        self.assertEqual(len(self.s["modes"]), 3)
        self.assertIsNone(self.s["modes"][1])
        self.assertEqual(se.normalize_studio({"modes": "x"})["modes"], [None, None, None])

    def test_modo_activo_sustituye_a_directo_y_hereda_lo_que_no_define(self):
        a, origin = se.resolve(self.s, "KEY_1", "x.exe", False, 0)
        self.assertEqual((origin, a["code"]), ("mode:0", 0x05))
        a, origin = se.resolve(self.s, "KEY_2", "x.exe", False, 0)    # el modo no define KEY_2 → Directo
        self.assertEqual((origin, a["code"]), ("base", 0x28))

    def test_la_regla_de_la_app_gana_al_modo(self):
        self.assertEqual(se.resolve(self.s, "KEY_1", "obs64.exe", True, 0)[1], "obs")
        self.assertEqual(se.resolve(self.s, "KEY_1", "obs64.exe", False, 0)[1], "mode:0")
        self.assertEqual(se.resolve(self.s, "KEY_2", "obs64.exe", True, 0)[1], "base")   # app sin KEY_2 y modo sin KEY_2

    def test_ctrl_shift_cambia_de_modo_y_repetir_vuelve_a_directo(self):
        with tempfile.TemporaryDirectory() as d:
            e = se.StudioEngine(simulate=True, path=Path(d) / "s.json")
            e.studio = self.s
            e.foreground = lambda: "x.exe"
            e.handle("KEY_1", False, True)
            self.assertEqual(e.active_mode, 0)
            e.handle("KEY_1", False)
            self.assertEqual(e.executed[-1][1], "mode:0")
            e.handle("KEY_2", False, True)            # hueco vacío: no cambia nada
            self.assertEqual(e.active_mode, 0)
            e.handle("KEY_1", False, True)
            self.assertIsNone(e.active_mode)
            self.assertEqual(e.status()["active_mode"], -1)
            e.handle("KNOB_CW", False, True)          # el acorde solo vale con los botones 1–3
            self.assertEqual(e.last["layer"], "base")

class NoticeTests(unittest.TestCase):
    def test_el_aviso_va_abajo_a_la_derecha_del_area_util(self):
        from volume_overlay import notice_origin
        # Pantalla 1920×1080 con barra de tareas de 48 px: el área útil termina en y=1032.
        self.assertEqual(notice_origin((0, 0, 1920, 1032), 280, 56), (1920 - 280 - 16, 1032 - 56 - 16))


class ChordTests(unittest.TestCase):
    def test_solo_ctrl_shift_es_el_acorde_de_modos(self):
        self.assertTrue(se.chord_held({"ctrl": True, "shift": True, "alt": False}))
        self.assertFalse(se.chord_held({"ctrl": False, "shift": True, "alt": True}))   # Alt+Shift ya no cambia de modo
        self.assertFalse(se.chord_held({"ctrl": True, "shift": False, "alt": False}))

@unittest.skipUnless(se.IS_WIN, "hook de teclado solo en Windows")
class HookTests(unittest.TestCase):
    def test_f13_con_shift_ejecuta_capa_de_app_y_se_traga(self):
        with tempfile.TemporaryDirectory() as d:
            eng = se.StudioEngine(simulate=True, accept_injected=True, path=Path(d) / "s.json")
            eng.foreground = lambda: "obs64.exe"
            eng.apply(STUDIO)
            self.assertTrue(eng.status()["running"], eng.error)
            try:
                se.key_down(0x10)               # Shift
                se.key_down(0x7C); se.key_up(0x7C)   # F13 = KEY_1
                se.key_up(0x10)
                se.key_down(0x7C); se.key_up(0x7C)   # sin Shift
                deadline = time.time() + 2
                while len(eng.executed) < 2 and time.time() < deadline:
                    time.sleep(0.02)
            finally:
                se.key_up(0x10)
                eng.stop()
            self.assertEqual([layer for _, layer in eng.executed], ["obs", "base"])
            self.assertEqual(eng.executed[0][0]["op"], "next_scene")


@unittest.skipUnless(se.IS_WIN, "hook de teclado solo en Windows")
class CaptureTests(unittest.TestCase):
    def test_graba_alt_tab_sin_dejarlo_pasar_y_libera_el_hook(self):
        with tempfile.TemporaryDirectory() as d:
            eng = se.StudioEngine(simulate=True, accept_injected=True, path=Path(d) / "s.json")
            self.assertTrue(eng.start_capture())
            try:
                se.key_down(0xA4); se.key_down(0x09); se.key_up(0x09); se.key_up(0xA4)   # Alt+Tab
                deadline = time.time() + 2
                while len(eng.capture_events()["events"]) < 4 and time.time() < deadline:
                    time.sleep(0.02)
                ev = eng.capture_events()["events"]
            finally:
                eng.stop_capture()
            self.assertEqual([(e.get("mod"), e.get("hid"), e["up"]) for e in ev],
                             [(4, None, False), (None, 0x2B, False), (None, 0x2B, True), (4, None, True)])
            self.assertIsNone(eng.hook, "el hook temporal debe cerrarse al terminar")
            self.assertFalse(eng.capture_events()["active"])


class FakeObs:
    """Servidor obs-websocket mínimo con autenticación, para probar el cliente."""

    def __init__(self, password):
        self.password, self.requests = password, []
        self.srv = socket.socket(); self.srv.bind(("127.0.0.1", 0)); self.srv.listen(1)
        self.port = self.srv.getsockname()[1]
        threading.Thread(target=self.serve, daemon=True).start()

    def send(self, c, obj):
        d = json.dumps(obj).encode()
        c.sendall(bytes([0x81, len(d)] if len(d) < 126 else [0x81, 126]) + (b"" if len(d) < 126 else struct.pack(">H", len(d))) + d)

    def recv(self, c):
        f = c.makefile("rb")
        b1, b2 = f.read(2)
        n = b2 & 0x7F
        n = struct.unpack(">H", f.read(2))[0] if n == 126 else n
        mask = f.read(4)
        return json.loads(bytes(b ^ mask[i % 4] for i, b in enumerate(f.read(n))))

    def serve(self):
        c, _ = self.srv.accept()
        buf = b""
        while b"\r\n\r\n" not in buf:
            buf += c.recv(1024)
        key = [l for l in buf.decode().split("\r\n") if l.lower().startswith("sec-websocket-key")][0].split(": ")[1]
        acc = base64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
        c.sendall(f"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: {acc}\r\n\r\n".encode())
        salt, challenge = "salt123", "chal456"
        self.send(c, {"op": 0, "d": {"obsWebSocketVersion": "5.0.0", "rpcVersion": 1,
                                     "authentication": {"challenge": challenge, "salt": salt}}})
        ident = self.recv(c)
        secret = base64.b64encode(hashlib.sha256((self.password + salt).encode()).digest()).decode()
        expect = base64.b64encode(hashlib.sha256((secret + challenge).encode()).digest()).decode()
        self.send(c, {"op": 2 if ident["d"].get("authentication") == expect else 5, "d": {}})
        data = {"GetSceneList": {"currentProgramSceneName": "B", "scenes": [
                    {"sceneName": "A", "sceneIndex": 2}, {"sceneName": "B", "sceneIndex": 1}, {"sceneName": "C", "sceneIndex": 0}]},
                "GetInputVolume": {"inputVolumeDb": -10.0}}
        while True:
            try:
                m = self.recv(c)
            except Exception:
                return
            d = m["d"]
            self.requests.append((d["requestType"], d["requestData"]))
            self.send(c, {"op": 7, "d": {"requestType": d["requestType"], "requestId": d["requestId"],
                                         "requestStatus": {"result": True, "code": 100}, "responseData": data.get(d["requestType"], {})}})


class ObsTests(unittest.TestCase):
    def client(self, srv, password):
        c = se.ObsClient()
        c.configure({"host": "127.0.0.1", "port": srv.port, "password": password})
        return c

    def test_escena_siguiente_y_volumen_con_autenticacion(self):
        srv = FakeObs("secreto")
        c = self.client(srv, "secreto")
        c.run(dict(OBS_NEXT))
        c.run({"op": "volume_up", "target": "Mic/Aux", "speed": 3})
        c.close()
        self.assertEqual(srv.requests[1], ("SetCurrentProgramScene", {"sceneName": "C"}))
        self.assertEqual(srv.requests[-1], ("SetInputVolume", {"inputName": "Mic/Aux", "inputVolumeDb": -7.0}))

    def test_contrasena_incorrecta(self):
        with self.assertRaises(ConnectionError):
            self.client(FakeObs("secreto"), "mala").run(dict(OBS_NEXT))


class ApiSecurityTests(unittest.TestCase):
    def setUp(self):
        app.StudioHandler.engine = se.StudioEngine(simulate=True, path=Path(tempfile.mkdtemp()) / "s.json")
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), app.StudioHandler)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.srv.server_port}"

    def tearDown(self):
        self.srv.shutdown(); self.srv.server_close()

    def post(self, path, body, headers=None, host=None):
        h = {"Content-Type": "application/json", **(headers or {})}
        if host:
            h["Host"] = host
        req = urllib.request.Request(self.base + path, json.dumps(body).encode(), h)
        try:
            return urllib.request.urlopen(req).status
        except urllib.error.HTTPError as e:
            return e.code

    def test_post_sin_cabecera_propia_se_rechaza(self):
        self.assertEqual(self.post("/api/run", {"action": K(0, 4)}), 403)

    def test_host_ajeno_se_rechaza(self):
        self.assertEqual(self.post("/api/run", {"action": K(0, 4)}, {"X-Studio": "1"}, host="evil.example"), 403)

    def test_window_solo_acciones_de_la_lista_blanca(self):
        calls, done = [], threading.Event()
        app.StudioHandler.window_control = lambda action: (calls.append(action), done.set())
        try:
            self.assertEqual(self.post("/api/window", {"action": "resize-se"}, {"X-Studio": "1"}), 200)
            self.assertTrue(done.wait(2))
            self.assertEqual(self.post("/api/window", {"action": "destroy"}, {"X-Studio": "1"}), 400)
            self.assertEqual(self.post("/api/window", {"action": "resize-xx"}, {"X-Studio": "1"}), 400)
        finally:
            app.StudioHandler.window_control = None
        self.assertEqual(calls, ["resize-se"])

    def test_guardar_config(self):
        self.assertEqual(self.post("/api/config", {"studio": STUDIO}, {"X-Studio": "1"}), 200)
        cfg = json.load(urllib.request.urlopen(self.base + "/api/config"))
        self.assertEqual(cfg["studio"]["layers"][1]["id"], "obs")


if __name__ == "__main__":
    unittest.main()
