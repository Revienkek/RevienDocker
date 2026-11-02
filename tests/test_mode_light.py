import threading
import unittest
from unittest.mock import Mock

from mode_light import ModeLight
from studio_engine import StudioEngine


class Timer:
    def __init__(self, interval, callback):
        self.interval, self.callback = interval, callback
        self.cancelled = False

    def start(self):
        pass

    def cancel(self):
        self.cancelled = True


class ModeLightTests(unittest.TestCase):
    def make_light(self, preference=0):
        writes = []
        light = ModeLight(lambda value: writes.append(value) or {"sent": True},
                          lambda: preference, threading.RLock(), Timer)
        return light, writes

    def test_off_and_cycle_restore_after_brief_notice(self):
        for preference in (0, 2):
            light, writes = self.make_light(preference)
            light.pulse()
            self.assertEqual(writes, [1])
            self.assertEqual(light.timer.interval, 0.45)
            light.timer.callback()
            self.assertEqual(writes, [1, preference])
            self.assertIsNone(light.timer)

    def test_new_notice_cancels_old_restore(self):
        light, writes = self.make_light()
        light.pulse()
        old = light.timer
        light.pulse()
        old.callback()  # Even if the cancelled callback was already waiting.
        self.assertTrue(old.cancelled)
        self.assertEqual(writes, [1, 1])
        light.timer.callback()
        self.assertEqual(writes, [1, 1, 0])

    def test_manual_setting_does_not_get_overwritten(self):
        light, writes = self.make_light()
        light.pulse()
        old = light.timer
        light.cancel()
        old.callback()
        self.assertEqual(writes, [1])

    def test_exit_restores_once_and_invalidates_timer(self):
        light, writes = self.make_light(2)
        light.pulse()
        old = light.timer
        light.close()
        old.callback()
        light.close()
        self.assertEqual(writes, [1, 2])

    def test_native_press_mode_needs_no_usb_writes(self):
        light, writes = self.make_light(1)
        light.pulse()
        self.assertEqual(writes, [])
        self.assertIsNone(light.timer)

    def test_missing_device_has_no_timer_and_failure_attempts_restore(self):
        light, _ = self.make_light()
        light.write = Mock(return_value={"sent": False})
        light.pulse()
        self.assertIsNone(light.timer)
        light.write = Mock(side_effect=OSError("unplugged"))
        light.pulse()
        self.assertEqual(light.write.call_count, 2)

    def test_engine_only_notifies_valid_physical_switches(self):
        engine = StudioEngine(simulate=True)
        engine.simulate = False
        engine.mode_light = Mock()
        engine.studio["modes"] = [{"name": "Music", "icon": "music"}, None, None]
        # Avoid the separate native screen notification during this unit test.
        with unittest.mock.patch("volume_overlay.show_message"):
            engine.set_mode(0, physical=True)
            self.assertEqual(engine.active_mode, 0)
            engine.set_mode(0, physical=True)
            self.assertIsNone(engine.active_mode)
            self.assertEqual(engine.mode_light.pulse.call_count, 2)
            engine.set_mode(1, physical=True)
            engine.set_mode(0)  # UI: no physical key to identify.
            self.assertEqual(engine.mode_light.pulse.call_count, 2)
