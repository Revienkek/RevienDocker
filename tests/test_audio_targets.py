import unittest
from unittest.mock import MagicMock, patch

import studio_engine as engine


class AudioTargetTests(unittest.TestCase):
    def test_physical_mode_switch_does_not_write_usb(self):
        instance = engine.StudioEngine(simulate=True)
        instance.simulate = False
        instance.mode_light = MagicMock()
        instance.studio["modes"] = [{"name": "Spotify", "icon": "music"}, None, None]
        with patch("volume_overlay.show_message"):
            instance.set_mode(0, physical=True)
            self.assertEqual(instance.active_mode, 0)
            instance.set_mode(0, physical=True)
            self.assertIsNone(instance.active_mode)
        instance.mode_light.pulse.assert_not_called()

    def test_audio_list_is_unique_and_skips_ended_process(self):
        first, second, ended = MagicMock(), MagicMock(), MagicMock()
        first.Process.name.return_value = "Spotify.exe"
        second.Process.name.return_value = "Spotify.exe"
        ended.Process.name.side_effect = OSError("closed")
        with patch("comtypes.CoInitialize"), patch("comtypes.CoUninitialize"), patch("pycaw.pycaw.AudioUtilities.GetAllSessions", return_value=[first, second, ended]):
            self.assertEqual(engine.list_audio_apps(), ["spotify.exe"])
