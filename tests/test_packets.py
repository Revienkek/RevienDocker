"""Pruebas sin hardware: `python -m unittest discover -s tests -t . -v`"""

import json
import threading
import unittest
import urllib.request
from http.server import HTTPServer

import app


class PacketTests(unittest.TestCase):
    def test_keyboard_packet(self):
        p = app.CH57xController.build_packet("KEY_1", "keyboard", 0x03, 0x68)
        self.assertEqual(len(p), 65)
        self.assertEqual(list(p[:7]), [0x03, 0x01, 0x11, 0x01, 0x01, 0x03, 0x68])

    def test_media_packet(self):
        p = app.CH57xController.build_packet("KNOB_CW", "media", 0, 0xE9)
        self.assertEqual(list(p[:5]), [0x03, 0x0F, 0x12, 0xE9, 0x00])

    def test_media_speed(self):
        p = app.CH57xController.build_packet("KNOB_CW", "media", 0, 0xE9, speed=3)
        self.assertEqual(list(p[:6]), [0x03, 0x0F, 0x12, 0xE9, 0x00, 0x03])

    def test_mouse_button_and_wheel(self):
        click = app.CH57xController.build_packet("KEY_1", "mouse", 0, 0x04)
        self.assertEqual(list(click[:6]), [0x03, 0x01, 0x13, 0x00, 0x04, 0x00])
        zoom_out = app.CH57xController.build_packet("KNOB_CCW", "mouse", 0x01, 0, wheel=-1, speed=2)
        self.assertEqual(list(zoom_out[:6]), [0x03, 0x0D, 0x13, 0x01, 0x00, 0xFE])

    def test_flash_sequence_simulated(self):
        c = app.CH57xController()
        c.connect = lambda: {"connected": False, "mode": "SIMULATOR"}
        maps = {k: {"type": "keyboard", "modifiers": 0, "hid_code": 104 + i}
                for i, k in enumerate(["KEY_1", "KEY_2", "KEY_3", "KNOB_CCW", "KNOB_CW", "KNOB_PRESS"])}
        logs = c.flash_mappings(maps, led_mode=2)
        tags = [l.split(":")[0] for l in logs[1:]]
        self.assertIn("UNLOCK_EEPROM", tags[0])
        self.assertIn("COMMIT_EEPROM", tags[-1])
        self.assertEqual(len(logs), 1 + 1 + 6 + 1 + 1)

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
