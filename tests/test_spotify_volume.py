import unittest
from unittest.mock import MagicMock, patch
import studio_engine as engine

class SpotifyVolumeTests(unittest.TestCase):
    def test_spotify_only_and_exact_step(self):
        spotify, other = MagicMock(), MagicMock()
        spotify.Process.name.return_value = "Spotify.exe"
        other.Process.name.return_value = "browser.exe"
        spotify.SimpleAudioVolume.GetMasterVolume.return_value = .5
        with patch("comtypes.CoInitialize"), patch("comtypes.CoUninitialize"), patch("pycaw.pycaw.AudioUtilities.GetAllSessions", return_value=[spotify, other]), patch("pycaw.pycaw.AudioUtilities.GetSpeakers") as master:
            engine.adjust_spotify_volume(0xEA, 3)
            spotify.SimpleAudioVolume.SetMasterVolume.assert_called_once_with(.47, None)
            other.SimpleAudioVolume.SetMasterVolume.assert_not_called()
            master.assert_not_called()

    def test_saved_spotify_mode_is_migrated(self):
        state = engine.normalize_studio({"modes": [{"name": "Spotify", "actions": {"KNOB_CW": {"type":"media", "code":233, "speed":5}}}]})
        action = state["modes"][0]["actions"]["KNOB_CW"]
        self.assertEqual((action["type"],action["target"],action["speed"]),("app_volume","spotify.exe",5))
