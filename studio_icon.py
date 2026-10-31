"""Genera los iconos de RevienDocker desde assets/Icon_definitivo.jpg (PNG HD + ICO multitamaño).

    python studio_icon.py        # escribe assets/icon.png y assets/icon.ico
"""

from pathlib import Path

from PIL import Image, ImageDraw

ASSETS = Path(__file__).resolve().parent / "assets"
SOURCE = ASSETS / "Icon_definitivo.jpg"
ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]
ART_SHARE = 0.84  # parte del lado que ocupa el dibujo; el resto es margen negro
TILE_RADIUS = 0.2  # esquina suave: ni 0 ni 90º
SUPERSAMPLE = 4  # la máscara se dibuja ampliada y se reduce: bordes suaves, sin escalera de píxeles


def _art_square() -> Image.Image:
    """Centra el dibujo en un cuadrado negro. El fondo de la ilustración ya es negro, así que se funde con el icono."""
    src = Image.open(SOURCE).convert("RGB")
    box = src.convert("L").point(lambda v: 255 if v > 30 else 0).getbbox()  # incluye el halo blanco
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    side = round(max(box[2] - box[0], box[3] - box[1]) / ART_SHARE)
    square = Image.new("RGB", (side, side), (0, 0, 0))
    square.paste(src, (round(side / 2 - cx), round(side / 2 - cy)))
    return square


def render(size: int) -> Image.Image:
    """Icono cuadrado RGBA de `size` px: dibujo centrado sobre negro, con esquinas suaves."""
    art = _art_square().resize((size, size), Image.LANCZOS).convert("RGBA")
    big = size * SUPERSAMPLE
    mask = Image.new("L", (big, big), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, big - 1, big - 1), radius=round(big * TILE_RADIUS), fill=255)
    art.putalpha(mask.resize((size, size), Image.LANCZOS))
    return art


def icon_image(size: int = 64) -> Image.Image:
    """Icono de la bandeja: usa el PNG ya generado (así el .exe no necesita el rasterizador SVG)."""
    from studio_engine import RESOURCE_DIR
    return Image.open(RESOURCE_DIR / "assets" / "icon.png").convert("RGBA").resize((size, size), Image.LANCZOS)


if __name__ == "__main__":
    render(1024).save(ASSETS / "icon.png")
    render(256).save(ASSETS / "icon.ico", sizes=[(s, s) for s in ICO_SIZES])
    print("OK", ASSETS / "icon.ico")
