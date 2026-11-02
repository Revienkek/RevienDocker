"""Pruebas de RevienDocker. El código vive en src/: se añade al path para importarlo como módulos."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
