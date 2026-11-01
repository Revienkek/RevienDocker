"""Pruebas sin hardware: `python -m unittest discover -s tests -t . -v`"""

import json
import threading
import unittest
import urllib.request
from http.server import HTTPServer

import app


def head(m, n=9):
    return list(m[:n])


class PacketTests(unittest.TestCase):
    """Formato verificado contra ch57x-keyboard-tool (CH57x 0x8890): mensajes de 64 bytes, Report ID 0x03."""

    def test_keyboard_key(self):
        msgs = app.CH57xController.key_messages("KEY_1", "keyboard", 0x01, 0x04)  # Ctrl+A
        self.assertTrue(all(len(m) == 64 for m in msgs))
        self.assertEqual(head(msgs[0], 5), [0x03, 0xFE, 0x01, 0x01, 0x01])
        self.assertEqual(head(msgs[1], 4), [0x03, 0x01, 0x11, 0x01])                 # tecla vacía previa
        self.assertEqual(head(msgs[2], 7), [0x03, 0x01, 0x11, 0x01, 0x01, 0x01, 0x04])
        self.assertEqual(head(msgs[3], 3), [0x03, 0xAA, 0xAA])

    def test_media_key(self):
        msgs = app.CH57xController.key_messages("KNOB_CW", "media", 0, 0xE9)
        self.assertEqual(head(msgs[1], 5), [0x03, 0x0F, 0x12, 0xE9, 0x00])

    def test_mouse_click_and_wheel(self):
        click = app.CH57xController.key_messages("KEY_3", "mouse", 0, 0x01)[1]
        self.assertEqual(head(click, 8), [0x03, 0x03, 0x13, 0x01, 0, 0, 0, 0])
        zoom = app.CH57xController.key_messages("KNOB_CCW", "mouse", 0x01, 0, wheel=-1, speed=2)[1]
        self.assertEqual(head(zoom, 8), [0x03, 0x0D, 0x13, 0x00, 0, 0, 0xFE, 0x01])

    def test_flash_sequence_simulated(self):
        c = app.CH57xController()
        c.connect = lambda: {"connected": False, "mode": "SIMULATOR"}
        maps = {k: {"type": "keyboard", "modifiers": 0, "hid_code": 104 + i}
                for i, k in enumerate(["KEY_1", "KEY_2", "KEY_3", "KNOB_CCW", "KNOB_CW", "KNOB_PRESS"])}
        logs = c.flash_mappings(maps, led_mode=2)
        self.assertEqual(len(logs), 1 + 6 * 4 + 3)          # estado + 6 botones x 4 mensajes + 3 de luz
        self.assertIn("LED", logs[-1])
        led = app.CH57xController.flash_messages({}, 2)
        self.assertEqual([head(m, 4) for _, m in led], [[3, 0xA1, 1, 0], [3, 0xB0, 0x18, 2], [3, 0xAA, 0xA1, 0]])

    def test_set_led_simulated(self):
        c = app.CH57xController()
        c.connect = lambda: {"connected": False, "mode": "SIMULATOR"}
        res = c.set_led(2)
        self.assertFalse(res["sent"])
        self.assertEqual(len(res["logs"]), 3)

    def test_write_error_is_reported(self):
        c = app.CH57xController()
        c.simulated = False
        class Dev:
            def write(self, _): return -1
            def error(self): return "boom"
        c.device = Dev()
        with self.assertRaises(OSError):
            c._send(bytes(64), [], "KEY_1")

    def test_http_flash_endpoint(self):
        srv = app.ThreadingHTTPServer(("127.0.0.1", 0), app.StudioHandler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{srv.server_port}"
        html = urllib.request.urlopen(base + "/index.html").read().decode("utf-8")
        self.assertIn("RevienDocker", html)
        body = json.dumps({"mappings": {"KEY_1": {"type": "keyboard", "modifiers": 0, "hid_code": 104}}}).encode()
        req = urllib.request.Request(base + "/api/flash", body, {"Content-Type": "application/json", "X-Studio": "1"})
        data = json.load(urllib.request.urlopen(req))
        self.assertTrue(data["ok"])
        srv.shutdown()


if __name__ == "__main__":
    unittest.main()
