"""Iconos propios de RevienDocker: apps y suites que la interfaz reconoce por el nombre del programa.

Dibujados a mano para este proyecto con la misma rejilla (24 px) y el mismo trazo que Lucide (el trazo lo pone `ic()`
en web/studio_icons.js). Evocan cada marca con una forma sencilla; no son sus logotipos oficiales ni proceden de
ningún paquete de iconos de terceros. Los nombres y marcas pertenecen a sus propietarios.

`build_icons.py` los junta con los de Lucide. En la interfaz no se ofrecen para elegir: solo salen cuando se
detecta el programa (véase APP_ICONS en web/studio.js).
"""

from math import cos, radians, sin


def _pt(r, deg, cx=12, cy=12):
    return cx + r * cos(radians(deg)), cy + r * sin(radians(deg))


def _burst(lengths, r0=2.2):
    """Rayos desde el centro (el destello de Claude)."""
    step = 360 / len(lengths)
    parts = []
    for i, r1 in enumerate(lengths):
        x0, y0 = _pt(r0, -90 + step * i)
        x1, y1 = _pt(r1, -90 + step * i)
        parts.append(f"M{x0:.2f} {y0:.2f}L{x1:.2f} {y1:.2f}")
    return f'<path d="{"".join(parts)}" />'


def _hex(r, start=-90):
    pts = [_pt(r, start + 60 * i) for i in range(6)]
    return "M" + "L".join(f"{x:.2f} {y:.2f}" for x, y in pts) + "z"


def _petals(n, ring, r):
    return " ".join(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r}" />' for x, y in (_pt(ring, -90 + 360 / n * i) for i in range(n)))


CIRCLE = '<circle cx="12" cy="12" r="10" />'
PAGE = '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /> <path d="M14 2v6h6" />'

CUSTOM = {
    # --- juegos y música (las plantillas de la app) ---
    "wow": CIRCLE + ' <path d="M7.5 8.5 9.8 15.5 12 11 14.2 15.5 16.5 8.5" />',
    "spotify": CIRCLE + ' <path d="M6.8 9.7c3.6-1.1 7.6-.8 10.7 1" /> <path d="M7.6 12.8c2.9-.8 6-.5 8.6 1" /> <path d="M8.4 15.7c2.3-.6 4.6-.4 6.6.7" />',
    "obs": CIRCLE + ' <path d="M10.58 6.69A5.5 5.5 0 0 1 17.31 10.58" /> <path d="M17.31 13.42A5.5 5.5 0 0 1 10.58 17.31" /> <path d="M8.11 15.89A5.5 5.5 0 0 1 8.11 8.11" />',
    # --- mensajería y reuniones ---
    "whatsapp": '<path d="M12 2a10 10 0 0 0-8.7 14.9L2 22l5.2-1.3A10 10 0 1 0 12 2z" /> <path d="M9 8.3c-.4 3.5 2.8 6.7 6.4 6.5l.9-1.4-2-1-.9.8a4 4 0 0 1-1.9-1.9l.8-.9-1-2z" />',
    "telegram": CIRCLE + ' <path d="M17.2 7.5 6.8 11.6l3.4 1.3 1.1 3.8 2.2-2.3 3.4 2.6z" /> <path d="M10.2 12.9l7-5.4" />',
    "discord": '<path d="M7 6.2a14 14 0 0 1 10 0c1.6 2.8 2.6 5.9 3 9.2a12 12 0 0 1-4.5 2.4l-1-2a10 10 0 0 1-5 0l-1 2A12 12 0 0 1 4 15.4c.4-3.3 1.4-6.4 3-9.200z" /> <circle cx="9" cy="12" r="1" /> <circle cx="15" cy="12" r="1" />',
    "slack": '<path d="M9.5 3.5V10M3.5 14.5H10M14.5 14V20.5M14 9.5H20.5" /> <path d="M14.5 4h.01M20 14.5h.01M9.5 20h.01M4 9.5h.01" />',
    "teams": '<rect x="2.5" y="5" width="12.5" height="14" rx="2" /> <path d="M5.8 9.5h6.4M9 9.5v6" /> <circle cx="18.2" cy="8" r="2" /> <path d="M15 10.5h4.2a2 2 0 0 1 2.3 2V16a2.5 2.5 0 0 1-2.5 2.5H15" />',
    "zoom": '<rect x="2.5" y="5" width="19" height="14" rx="4" /> <path d="M7 10.5h5.2v3a1 1 0 0 1-1 1H7zM12.2 12.5 16.5 10v4.6z" />',
    # --- navegadores ---
    "chrome": CIRCLE + ' <circle cx="12" cy="12" r="4" /> <path d="M15.46 10 20.66 7M12 16v6M8.54 10 3.34 7" />',
    "edge": '<path d="M20.6 15A9 9 0 1 0 12 21c2.3 0 4.4-.9 6-2.4" /> <path d="M6.5 13H17a5 5 0 1 0-9.4 2.4" />',
    "firefox": '<path d="M12 21a9 9 0 0 1-7.2-14.4C5 7.800 5.600 9 7 9.400 7.400 6.800 9.300 4.600 12 3.600c.300 1.800 1.500 2.800 3 3.600 2.600 1.300 5.700 3 5.700 7.200A8.700 8.700 0 0 1 12 21z" /> <path d="M8.5 14.5a3.500 3.500 0 0 0 7 0" />',
    "opera": CIRCLE + ' <ellipse cx="12" cy="12" rx="3.6" ry="6.4" />',
    "brave": '<path d="M12 21.5 5 18V8.500L7 4h10l2 4.500V18z" /> <path d="M9 10l3 1.500L15 10M12 11.500V16" />',
    # --- asistentes ---
    "claude": _burst([9.6, 6.6, 8.6, 6.6, 9.6, 6.6, 8.6, 6.6, 9.6, 6.6, 8.6, 6.6]),
    "chatgpt": f'<path d="{_hex(9.6)}" /> <path d="{_hex(4.6, -60)}" /> <path d="M12 7.400V2.400M16 9.700l4.300-2.500M16 14.300l4.300 2.500M12 16.600v5M8 14.300l-4.300 2.500M8 9.700 3.700 7.200" />',
    # --- oficina y creación (por suites) ---
    "word": PAGE + ' <path d="M8 12.500l1.400 5L12 13.500l2.600 4 1.400-5" />',
    "excel": PAGE + ' <path d="M9 12.500l6 6M15 12.500l-6 6" />',
    "powerpoint": PAGE + ' <path d="M10 18.500v-6h2.600a2 2 0 0 1 0 4H10" />',
    "office": '<rect x="3" y="3" width="8.500" height="8.500" rx="1.200" /> <rect x="12.500" y="3" width="8.500" height="8.500" rx="1.200" /> <rect x="3" y="12.500" width="8.500" height="8.500" rx="1.200" /> <rect x="12.500" y="12.500" width="8.500" height="8.500" rx="1.200" />',
    "notion": '<rect x="3.500" y="3.500" width="17" height="17" rx="3" /> <path d="M9 16.500V8l6 8.500V7.500" />',
    "vscode": '<path d="M17 3l4 1.800v14.400L17 21 7.500 12.500 3.500 15.500 2.200 14.700V9.300l1.300-.8 4 3L17 3z" /> <path d="M17 3v18" />',
    "adobe": '<path d="M2.500 20.500 8 3.500H2.500z" /> <path d="M21.500 20.500 16 3.500h5.500z" /> <path d="M12 9.500l3.700 11h-2.800l-1-2.800H9.700z" />',
    "google": CIRCLE + ' <path d="M16.140 8.530A5.400 5.400 0 1 0 17.400 12H12" />',
    "figma": '<path d="M12 1.500H8.500a3.500 3.500 0 0 0 0 7H12z" /> <path d="M12 1.500h3.500a3.500 3.500 0 0 1 0 7H12z" /> <path d="M12 8.500H8.500a3.500 3.500 0 0 0 0 7H12z" /> <circle cx="15.500" cy="12" r="3.500" /> <path d="M12 15.500H8.500a3.500 3.500 0 1 0 3.500 3.500z" />',
    "obsidian": '<path d="M12 2.500 19 8l-2.200 12.500L9.500 22 5 11.500z" /> <path d="M12 2.500 9.500 22M5 11.500l11.800 9M19 8l-14 3.500" />',
    "davinci": CIRCLE + " " + _petals(5, 4.4, 2.2),
    "blender": '<path d="M11 9.500 3 15.500" /> <path d="M3 15.500h5" /> <circle cx="15" cy="14" r="5.500" /> <circle cx="15" cy="14" r="2" />',
    # --- juegos y vídeo ---
    "steam": CIRCLE + ' <circle cx="15.500" cy="9.500" r="2.700" /> <circle cx="8.800" cy="15.600" r="1.800" /> <path d="M10.400 14.600l3.400-3.200" />',
    "epic": '<path d="M5 3h14v14l-7 4.500L5 17z" /> <path d="M15 8.500H9.500v6H15M9.500 11.500h4" />',
    "battlenet": CIRCLE + ' <path d="M12 6.800a5.200 5.200 0 1 1-5.200 5.200c0-2.200 1.700-3.400 3.400-3.400s2.600 1.200 2.600 2.400" />',
    "vlc": '<path d="M12 3 20 20.500H4z" /> <path d="M9.200 9.800h5.600M7.300 14.800h9.400" />',
    "twitch": '<path d="M4 3h17v11l-4 4h-4l-3 3v-3H4z" /> <path d="M12 7.500v4M16.500 7.500v4" />',
    "minecraft": '<path d="M12 2.500 20.500 7v10L12 21.500 3.500 17V7z" /> <path d="M12 12 3.500 7M12 12l8.500-5M12 12v9.500" />',
}
