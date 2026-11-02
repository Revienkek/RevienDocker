"""El indicador no programa sondeos; cada aviso reinicia solo su cierre."""
import queue
import sys
import unittest
from unittest.mock import MagicMock, patch
import volume_overlay as overlay


class IdleNoticeTests(unittest.TestCase):
    def test_notices_render_and_hide_without_polling(self):
        root, canvas, user32 = MagicMock(), MagicMock(), MagicMock()
        timers, bindings, pending = {}, {}, queue.Queue()
        pending.put(("volume", 37))
        root.after.side_effect = lambda delay, callback: timers.setdefault(len(timers), (delay, callback)) or 0
        root.bind.side_effect = lambda event, callback: bindings.update({event: callback})
        root.winfo_screenwidth.return_value = 1920
        root.winfo_screenheight.return_value = 1080
        # Ejercita el receptor de Tk sin depender de una pantalla ni tocar audio.
        class InlineThread:
            def __init__(self, target, **kwargs): self.target = target
            def start(self): self.target()
        class EndDispatch(Exception): pass
        def event_generate(*args, **kwargs):
            bindings["<<DockerNotice>>"]()
            raise EndDispatch()
        root.event_generate.side_effect = event_generate
        def loop():
            try: timers[0][1]()
            except EndDispatch: pass
        root.mainloop.side_effect = loop
        tk = MagicMock(Tk=MagicMock(return_value=root), Canvas=MagicMock(return_value=canvas))
        tk.TclError = RuntimeError
        with patch.dict(sys.modules, {"tkinter": tk}), patch.object(overlay, "_values", pending), \
             patch.object(overlay.threading, "Thread", InlineThread), \
             patch.object(overlay.ctypes, "windll", MagicMock(user32=user32), create=True), \
             patch.object(overlay, "_work_area", return_value=(0, 0, 1920, 1080)):
            overlay._run()
        delays = [delay for delay, _ in timers.values()]
        self.assertEqual(delays, [0, 1800])
        canvas.itemconfigure.assert_any_call(canvas.create_text.return_value, text="37")
        user32.SetWindowPos.assert_called_once()
        timers[1][1]()
        user32.ShowWindow.assert_called_once()
