import re
import unittest
from pathlib import Path

from version import __version__

ROOT = Path(__file__).resolve().parent.parent


class VersionTests(unittest.TestCase):
    def test_el_changelog_empieza_por_la_version_actual(self):
        texto = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        primera = re.search(r"^## \[(\d+\.\d+\.\d+)\]", texto, re.M)
        self.assertIsNotNone(primera)
        self.assertEqual(primera.group(1), __version__)


if __name__ == "__main__":
    unittest.main()
