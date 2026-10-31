"""Genera assets/wordmark.svg: «REVIENDOCKER» en vector, con las letras de Doris PP convertidas a trazos.

    python studio_wordmark.py                      # usa Doris PP instalada en Windows
    python studio_wordmark.py ruta\\DorisPP.ttf    # o una ruta concreta
"""

import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ASSETS = Path(__file__).resolve().parent / "assets"
DEFAULT_FONT = Path.home() / "AppData" / "Local" / "Microsoft" / "Windows" / "Fonts" / "DorisPP.ttf"
TEXT = "REVIENDOCKER"
TRACKING = 0.06  # em, igual que el interletrado del título en CSS
# Degradado de opacidades en blanco (el «metal» del título).
STOPS = [(0, 1.0), (0.26, 0.5), (0.42, 1.0), (0.6, 0.28), (0.78, 1.0), (1, 0.62)]


def build(font_path: Path) -> str:
    font = TTFont(font_path)
    upm = font["head"].unitsPerEm
    cmap, glyphs, hmtx = font.getBestCmap(), font.getGlyphSet(), font["hmtx"]
    cap = getattr(font["OS/2"], "sCapHeight", 0) or round(upm * 0.7)  # tablas OS/2 antiguas no lo traen
    pad = round(upm * 0.02)  # margen para que no se recorten las curvas de O, C y S

    pen = SVGPathPen(glyphs)
    x = 0
    for char in TEXT:
        name = cmap[ord(char)]
        glyphs[name].draw(TransformPen(pen, (1, 0, 0, -1, x, 0)))  # la fuente va hacia arriba; SVG hacia abajo
        x += hmtx[name][0] + TRACKING * upm
    width = x - TRACKING * upm

    stops = "".join(
        f'<stop offset="{off}" stop-color="#fff" stop-opacity="{op}"/>' for off, op in STOPS
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-pad} {-cap - pad} {width + 2 * pad:.0f} {cap + 2 * pad}">'
        f'<defs><linearGradient id="metal" x1="0" y1="0" x2="1" y2="0.2">{stops}</linearGradient></defs>'
        f'<path d="{pen.getCommands()}" fill="url(#metal)" stroke="#fff" stroke-opacity="0.3" '
        f'stroke-width="{upm * 0.02:.0f}" stroke-linejoin="round"/>'
        "</svg>\n"
    )


if __name__ == "__main__":
    font = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FONT
    out = ASSETS / "wordmark.svg"
    out.write_text(build(font), encoding="utf-8")
    print("OK", out)
