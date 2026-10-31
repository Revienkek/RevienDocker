"""Genera los iconos de RevienDocker a partir de assets/icon.svg (SVG → PNG HD + ICO multitamaño).

    python studio_icon.py        # escribe assets/icon.png y assets/icon.ico
"""

import io
from pathlib import Path

from PIL import Image

ASSETS = Path(__file__).resolve().parent / "assets"


def render(size: int = 1024) -> Image.Image:
    import resvg_py  # solo hace falta al regenerar los iconos
    png = resvg_py.svg_to_bytes(svg_path=str(ASSETS / "icon.svg"), width=size, height=size)
    return Image.open(io.BytesIO(bytes(png))).convert("RGBA")


def icon_image(size: int = 64) -> Image.Image:
    """Icono de la bandeja: usa el PNG ya generado (así el .exe no necesita el rasterizador SVG)."""
    from studio_engine import RESOURCE_DIR
    return Image.open(RESOURCE_DIR / "assets" / "icon.png").convert("RGBA").resize((size, size), Image.LANCZOS)


if __name__ == "__main__":
    master = render(1024)
    master.save(ASSETS / "icon.png")
    master.save(ASSETS / "icon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("OK", ASSETS / "icon.ico")
