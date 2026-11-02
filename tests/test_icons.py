import importlib.util
import re
import unittest
from pathlib import Path

from volume_overlay import GLYPHS

ROOT = Path(__file__).resolve().parent.parent


def _custom_icons():
    spec = importlib.util.spec_from_file_location("custom_icons", ROOT / "tools" / "custom_icons.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.CUSTOM


class IconTests(unittest.TestCase):
    def test_todo_icono_propio_tiene_glifo_en_el_aviso_nativo(self):
        faltan = [n for n in _custom_icons() if n not in GLYPHS]
        self.assertEqual(faltan, [])

    def test_el_selector_ofrece_exactamente_los_iconos_propios(self):
        js = (ROOT / "web" / "studio.js").read_text(encoding="utf-8")
        bloque = re.search(r"const APP_ICON_PICKS = \[(.*?)\];\s*function iconPicker", js, re.S).group(1)
        self.assertEqual(sorted(re.findall(r'\["([a-z0-9-]+)",', bloque)), sorted(_custom_icons()))


if __name__ == "__main__":
    unittest.main()
