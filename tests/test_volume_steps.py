"""Pasos de volumen y selección del motor, sin tocar el audio real."""

import unittest
from unittest.mock import MagicMock, patch

import studio_engine as engine


@unittest.skipUnless(engine.IS_WIN, "Core Audio solo está disponible en Windows")
class VolumeStepTests(unittest.TestCase):
    def test_absolute_volume_steps_and_limits(self):
        endpoint = MagicMock()
        device = MagicMock()
        device.EndpointVolume = endpoint
        with patch("comtypes.CoInitialize"), patch("comtypes.CoUninitialize"), \
                patch("pycaw.pycaw.AudioUtilities.GetSpeakers", return_value=device):
            for code, start, step, expected in ((0xE9, .40, 1, .41), (0xE9, .40, 2, .42),
                                                (0xEA, .40, 3, .37), (0xEA, .40, 5, .35),
                                                (0xE9, .98, 5, 1.0), (0xEA, .02, 5, 0.0)):
                with self.subTest(code=code, step=step, start=start):
                    endpoint.GetMasterVolumeLevelScalar.return_value = start
                    engine.adjust_system_volume(code, step)
                    endpoint.SetMasterVolumeLevelScalar.assert_called_with(expected, None)

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
