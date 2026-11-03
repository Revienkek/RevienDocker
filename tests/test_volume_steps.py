"""Pasos de volumen nativos y selección del motor, sin tocar el audio real."""

import unittest
from unittest.mock import MagicMock, patch

import studio_engine as engine


@unittest.skipUnless(engine.IS_WIN, "Teclas multimedia nativas disponibles en Windows")
class VolumeStepTests(unittest.TestCase):
    def test_native_volume_steps(self):
        with patch.object(engine, "run_media") as mock_run_media:
            for code, speed in ((0xE9, 1), (0xE9, 2), (0xEA, 3), (0xEA, 5)):
                with self.subTest(code=code, speed=speed):
                    engine.adjust_system_volume(code, speed)
                    mock_run_media.assert_called_with(code, speed)

    def test_run_media_sends_native_keys(self):
        with patch.object(engine, "_send") as mock_send, patch.object(engine.time, "sleep"):
            # 0xE9 es Vol Up -> VK 0xAF
            engine.run_media(0xE9, 2)
            self.assertEqual(mock_send.call_count, 2)

    def test_volume_wheel_always_goes_through_engine(self):
        e = engine.StudioEngine(simulate=True)
        e.foreground = lambda: "example.exe"
        volume = {"type": "media", "code": 0xE9, "speed": 3, "mod": 0, "wheel": 0}
        e.studio = engine.normalize_studio({"layers": [{"id": "base", "actions": {"KNOB_CW": volume}}]})
        e.handle("KNOB_CW", False)
        self.assertEqual(e.executed[0][0]["speed"], 3)
        e.handle("KEY_1", False)
        self.assertEqual(len(e.executed), 1)


if __name__ == "__main__":
    unittest.main()
