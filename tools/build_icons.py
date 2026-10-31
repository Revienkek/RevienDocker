"""Genera studio_icons.js con los iconos de Lucide que usa la interfaz (inline, sin red ni CDN).

Fuente: paquete npm `lucide-static` (licencia ISC, https://lucide.dev).
    npm i -g lucide-static
    python tools/build_icons.py
"""

import json
import os
import re
import subprocess
from pathlib import Path

NAMES = """keyboard mouse mouse-pointer-click music clapperboard zap plug brain target layers plus trash-2 play circle-dot minus x
square copy rotate-ccw volume-2 scroll zoom-in app-window undo-2 skip-forward brush mic settings-2 chevron-right chevron-down
arrow-right sparkles ghost code-xml sliders-horizontal lightbulb terminal panel-top film gauge arrow-left-right info check
command monitor-up circle-help cable save pointer bolt gamepad-2 layout-grid hash plug-zap flame wand-sparkles circle-alert""".split()

ROOT = Path(subprocess.check_output("npm root -g", shell=True, text=True).strip()) / "lucide-static" / "icons"
OUT = Path(__file__).resolve().parent.parent / "studio_icons.js"

icons, missing = {}, []
for n in NAMES:
    f = ROOT / f"{n}.svg"
    if not f.exists():
        missing.append(n)
        continue
    inner = re.sub(r"<!--.*?-->", "", f.read_text(encoding="utf-8"), flags=re.S)
    inner = re.search(r"<svg[^>]*>(.*)</svg>", inner, flags=re.S).group(1)
    icons[n] = re.sub(r"\s+", " ", inner).strip()

OUT.write_text(
    "/* Iconos Lucide (ISC) — generado por tools/build_icons.py */\n"
    "window.ICONS = " + json.dumps(icons, ensure_ascii=False) + ";\n"
    "window.ic = (name, cls = '') => `<svg class=\"ic ${cls}\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" "
    "stroke-width=\"1.8\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\">${ICONS[name] || ''}</svg>`;\n"
    "window.hydrateIcons = (root = document) => root.querySelectorAll('[data-ic]').forEach(e => { e.innerHTML = ic(e.dataset.ic); e.removeAttribute('data-ic'); });\n",
    encoding="utf-8")
print(f"{len(icons)} iconos -> {OUT}", "| faltan:", missing or "ninguno")
