"""Genera los iconos de RevienDocker a partir de assets/ICON.jpg (PNG HD + ICO multitamaño).

    python studio_icon.py        # escribe assets/icon.png y assets/icon.ico
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

ASSETS = Path(__file__).resolve().parent / "assets"


def render(size: int = 1024) -> Image.Image:
    """Recorta el dibujo (fondo blanco fuera), lo centra en un cuadrado y lo redondea con una esquina suave."""
    rgb = Image.open(ASSETS / "ICON.jpg").convert("RGB")
    box = rgb.convert("L").point(lambda v: 255 if v < 200 else 0).getbbox()
    pad = int(max(box[2] - box[0], box[3] - box[1]) * 0.04)
    box = (max(0, box[0] - pad), max(0, box[1] - pad), min(rgb.width, box[2] + pad), min(rgb.height, box[3] + pad))
    art = ImageOps.pad(rgb.crop(box), (size, size), color=(255, 255, 255), method=Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=int(size * 0.18), fill=255)
    out = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    out.paste(art.convert("RGBA"), (0, 0), mask)
    return out


def icon_image(size: int = 64) -> Image.Image:
    """Icono de la bandeja: usa el PNG ya generado (así el .exe no necesita el rasterizador SVG)."""
    from studio_engine import RESOURCE_DIR
    return Image.open(RESOURCE_DIR / "assets" / "icon.png").convert("RGBA").resize((size, size), Image.LANCZOS)


if __name__ == "__main__":
    master = render(1024)
    master.save(ASSETS / "icon.png")
    master.save(ASSETS / "icon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("OK", ASSETS / "icon.ico")
