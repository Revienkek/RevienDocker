# RevienDocker

Programa de escritorio (Windows) para configurar el macropad acrílico de 3 teclas + 1 rueda (WCH CH57x / CH552, VID `0x1189` / PID `0x8890`) sin el ejecutable del fabricante.

- **Modo Directo:** las asignaciones (teclas, ratón, multimedia) se graban en la memoria del teclado.
- **Modo Inteligente:** cada botón cambia según la app en primer plano (capas por app, acciones nativas de OBS por WebSocket). Corre en tu PC y se queda en la bandeja.
- Grabación real de combinaciones (incluidas Alt+Tab y Win), botones del ratón, recetas de rueda con velocidad.

Guía de uso: [GUIA_USUARIO.md](GUIA_USUARIO.md).

> Estado: probado con simuladores y pruebas automáticas. Las tramas USB de ratón, multimedia con repeticiones y velocidad son extensiones propias **no verificadas** contra el firmware real.

## Estructura

| Ruta | Qué es |
|---|---|
| `index.html`, `studio.css`, `studio.js`, `studio_icons.js` | Interfaz (sin dependencias) |
| `app.py` | Servidor local `127.0.0.1:8765`, API y flasheo USB HID (`hidapi`, con simulador automático) |
| `studio_engine.py` | Motor inteligente: hook F13–F18, capas por app, SendInput, cliente OBS WebSocket, captura de teclado |
| `studio_app.py` | App de escritorio: ventana sin marco (pywebview), bandeja, instancia única |
| `studio_icon.py`, `assets/` | Icono (`icon.svg` es la fuente; `icon.png/.ico` se generan) |
| `tools/build_icons.py` | Genera `studio_icons.js` con iconos [Lucide](https://lucide.dev) (licencia ISC) |
| `tests/` | Pruebas sin hardware ni OBS |
| `build_exe.ps1` | Compila `dist\RevienDocker.exe` |

**Seguridad:** la API solo acepta Host local y exige la cabecera `X-Studio`, así que una web externa no puede pulsar teclas en tu PC.

## Uso

```bash
pip install -r requirements.txt
python studio_app.py        # app de escritorio
python start_studio.py      # solo servidor + navegador (desarrollo)
```

Compilar el `.exe`:

```bash
pip install -r requirements-dev.txt
powershell -ExecutionPolicy Bypass -File build_exe.ps1
```

- `RevienDocker.exe --minimized` arranca oculto en la bandeja (acceso directo en `shell:startup` para que arranque con Windows).
- Tu configuración queda en `%APPDATA%\RevienDocker\studio.json` (en desarrollo, `studio.json` junto al código).
- Cerrar la ventana: en modo Inteligente se oculta en la bandeja; en Directo, sale.

Pruebas:

```bash
python -m unittest discover -s tests -t . -v
```

## Protocolo USB HID (0x1189:0x8890)

Interfaz con Usage Page `0xFF00`, tramas de 65 bytes (Report ID `0x03` + 64 de payload).

| Botón | Slot (byte 1) |
|---|---|
| KEY_1 / KEY_2 / KEY_3 | `0x01` / `0x02` / `0x03` |
| KNOB_CCW / KNOB_PRESS / KNOB_CW | `0x0D` / `0x0E` / `0x0F` |

Secuencia: unlock `03 A1 01` → una escritura por botón → LED `03 A2 <modo 0-3>` → commit `03 AA AA`.

- Tecla: `03 <slot> 11 01 01 <mod> <código>`
- Multimedia: `03 <slot> 12 <lo> <hi> <repeticiones>`
- Ratón: `03 <slot> 13 <mod> <botones> <rueda con signo>` (botones: 1 izq, 2 der, 4 central, 8 atrás, 16 adelante)

Tecla, multimedia, LED y commit vienen de la documentación original; ratón, repeticiones y velocidad son extensiones propias.

## Licencias

Iconos de interfaz: Lucide (ISC). El proyecto aún no tiene licencia propia: elige una antes de publicarlo.
