"""Genera los recursos de icono a partir de la ilustración definitiva."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

ASSETS = Path(__file__).resolve().parent.parent / "web" / "assets"
SOURCE = ASSETS / "Icon_definitivo.jpg"
ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]


def artwork() -> Image.Image:
    """Quita el negro exterior conservando las zonas negras dentro del contorno."""
    src = Image.open(SOURCE).convert("RGB")
    luminance = ImageOps.grayscale(src)
    # El contorno blanco separa el fondo de las piezas negras del dispositivo.
    barriers = luminance.point(lambda value: 255 if value > 45 else 0)
    ImageDraw.floodfill(barriers, (0, 0), 128)
    outside = barriers.point(lambda value: 255 if value == 128 else 0)
    # En el exterior, el halo blanco se desvanece hacia transparencia.
    halo = luminance.point(lambda value: min(255, value * 4))
    alpha = Image.composite(halo, Image.new("L", src.size, 255), outside)
    image = src.convert("RGBA")
    image.putalpha(alpha)
    box = alpha.point(lambda value: 255 if value > 32 else 0).getbbox()
    if box is None:
        raise ValueError("No se ha encontrado el dispositivo en la imagen")
    return image.crop(box)


def render(size: int) -> Image.Image:
    """Composición cuadrada para Windows, ajustada al ancho disponible."""
    art = artwork()
    art.thumbnail((round(size * 0.97), round(size * 0.97)), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size))
    canvas.alpha_composite(art, ((size - art.width) // 2, (size - art.height) // 2))
    return canvas


def icon_image(size: int = 64) -> Image.Image:
    """Icono de la bandeja incluido en el ejecutable."""
    from studio_engine import RESOURCE_DIR
    return Image.open(RESOURCE_DIR / "assets" / "icon.png").convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)


if __name__ == "__main__":
    art = artwork()
    art.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
    art.save(ASSETS / "brand-icon.png")
    render(1024).save(ASSETS / "icon.png")
    render(256).save(ASSETS / "icon.ico", sizes=[(s, s) for s in ICO_SIZES])
    print("OK: icon.png, icon.ico y brand-icon.png")
