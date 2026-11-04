"""
studio_engine.py — Motor inteligente de RevienDocker (solo Windows para la parte de entrada).

Cómo funciona RevienDocker (el docker y la app son un solo sistema):
  1. El macropad se prepara una vez para emitir teclas fantasma F13–F18 (una por botón / giro de rueda).
  2. Este motor instala un hook de teclado de bajo nivel que SOLO mira esas seis teclas
     (las traga para que ninguna app las vea) y recuerda si la tecla de activación
     (Shift / Ctrl / Alt) está pulsada físicamente.
  3. En un hilo aparte decide qué hacer. Prioridad: con la tecla de activación y una capa para la app en
     primer plano, esa capa; si no, el modo activo (si lo hay); si no, la capa «base» (Directo).
     Ctrl+Shift + botón 1/2/3 activa el modo 1/2/3; repetirlo vuelve a Directo.
  4. La acción se ejecuta por SendInput (teclado, ratón, multimedia) o por OBS WebSocket.

No hay sondeo: el motor está dormido hasta que llega una tecla fantasma.
"""

import base64
import hashlib
import json
import os
import queue
import re
import socket
import struct
import sys
import threading
import time
from collections import deque
from pathlib import Path

IS_WIN = sys.platform == "win32"
FROZEN = getattr(sys, "frozen", False)
ROOT_DIR = Path(__file__).resolve().parent.parent
# Interfaz (index.html, css, js, assets): carpeta web/ del repositorio o, empaquetado, web/ dentro del .exe
RESOURCE_DIR = (Path(sys._MEIPASS) / "web") if hasattr(sys, "_MEIPASS") else ROOT_DIR / "web"
# Empaquetado como .exe, la configuración vive en %APPDATA% (junto al .exe no hay permiso de escritura asegurado)
DATA_DIR = (Path(os.environ.get("APPDATA", Path.home())) / "RevienDocker") if FROZEN else ROOT_DIR
DATA_DIR.mkdir(parents=True, exist_ok=True)
_OLD = Path(os.environ.get("APPDATA", Path.home())) / "BotoneraStudio" / "studio.json"  # nombre anterior del proyecto
if FROZEN and _OLD.exists() and not (DATA_DIR / "studio.json").exists():
    (DATA_DIR / "studio.json").write_bytes(_OLD.read_bytes())
STUDIO_FILE = DATA_DIR / "studio.json"

SLOTS = ("KEY_1", "KEY_2", "KEY_3", "KNOB_CCW", "KNOB_CW", "KNOB_PRESS")
MODE_SLOTS = 3
DIRECT_SLOTS = 3  # accesos a perfiles en el carril de Directo
MY_MODES_MAX = 3  # «Mis modos»: modos propios guardados, reutilizables en cualquier hueco
MODE_KEYS = ("KEY_1", "KEY_2", "KEY_3")   # con Ctrl+Shift activan el modo 1, 2 o 3
GHOST_VK = {0x7C: "KEY_1", 0x7D: "KEY_2", 0x7E: "KEY_3", 0x7F: "KNOB_CCW", 0x80: "KNOB_CW", 0x81: "KNOB_PRESS"}
TRIGGER_VKS = {"shift": {0x10, 0xA0, 0xA1}, "ctrl": {0x11, 0xA2, 0xA3}, "alt": {0x12, 0xA4, 0xA5}}
TRIGGER_VK = {"shift": 0x10, "ctrl": 0x11, "alt": 0x12}
MOD_VK = ((1, 0x11), (2, 0x10), (4, 0x12), (8, 0x5B))  # Ctrl, Shift, Alt, Win


def chord_held(phys):
    """Ctrl+Shift físicos: cambio de modo. Alt ya no interviene (es de Windows y de los menús)."""
    return bool(phys.get("ctrl") and phys.get("shift"))
OBS_OPS = ("next_scene", "prev_scene", "scene", "toggle_source", "toggle_mute",
           "volume_up", "volume_down", "toggle_record", "toggle_stream")

DEFAULT_STUDIO = {
    "mode": "direct",               # solo recuerda la pestaña abierta; el motor siempre funciona igual
    "trigger": "shift",
    "led_mode": 1,
    "flashed": "",
    "applied": None,
    "modes": [None, None, None],
    "library": [],
    "profiles": [],
    "direct_slots": [None, None, None],
    "active_profile": None,
    "layers": [{"id": "base", "name": "Base", "exes": [], "actions": {}}],
    "obs": {"host": "127.0.0.1", "port": 4455, "password": ""},
}


# ----------------------------------------------------------------------------- configuración
def _int(v, lo, hi, default=0):
    try:
        return max(lo, min(hi, int(v)))
    except (TypeError, ValueError):
        return default


def _clean_action(a):
    if not isinstance(a, dict):
        return None
    t = a.get("type")
    if t not in ("keyboard", "media", "mouse", "obs", "app_volume"):
        return None
    out = {"type": t, "mod": _int(a.get("mod"), 0, 15), "code": _int(a.get("code"), 0, 0xFFFF),
           "wheel": _int(a.get("wheel"), -1, 1), "speed": _int(a.get("speed"), 1, 10, 1)}
    if t == "app_volume":
        if out["code"] not in (0xE9, 0xEA, 0xE2):
            return None
        target = str(a.get("target") or "spotify.exe").strip().lower()
        out["target"] = target if re.fullmatch(r"[^\\/:*?\"<>|]{1,76}\.exe", target) else "spotify.exe"
    if t == "obs":
        op = a.get("op")
        if op not in OBS_OPS:
            return None
        out["op"] = op
        out["target"] = str(a.get("target", ""))[:80]
    return out


def _clean_actions(raw):
    acts = {}
    for slot, a in (raw if isinstance(raw, dict) else {}).items():
        c = _clean_action(a)
        if slot in SLOTS and c:
            acts[slot] = c
    return acts


def _clean_mode(m, n):
    icon = re.sub(r"[^a-z0-9-]", "", str(m.get("icon", "")).lower())[:30] or "sliders-horizontal"
    return {"name": str(m.get("name", ""))[:30] or f"Modo {n}", "icon": icon, "actions": _clean_actions(m.get("actions"))}


def _clean_id(raw):
    return re.sub(r"[^a-z0-9_-]", "", str(raw or "").lower())[:40]


def _clean_library(raw):
    """Mis modos: hasta MY_MODES_MAX modos propios {id, name, icon, actions}. El id enlaza cada hueco con su copia guardada."""
    out, seen = [], set()
    for m in (raw if isinstance(raw, list) else []):
        mid = _clean_id(m.get("id")) if isinstance(m, dict) else ""
        if not mid or mid in seen or len(out) >= MY_MODES_MAX:
            continue
        seen.add(mid)
        out.append({"id": mid, **_clean_mode(m, len(out) + 1)})
    return out


def _clean_modes(raw, library_ids=()):
    """Tres huecos (Ctrl+Shift+1/2/3); cada uno vacío (None) o un modo {name, icon, actions[, from]}.
    «from» es el id de su copia en Mis modos; si esa copia ya no existe, se descarta."""
    raw = raw if isinstance(raw, list) else []
    out = []
    for i in range(MODE_SLOTS):
        m = raw[i] if i < len(raw) else None
        if isinstance(m, dict):
            mode = _clean_mode(m, i + 1)
            if _clean_id(m.get("from")) in library_ids:
                mode["from"] = _clean_id(m.get("from"))
            out.append(mode)
        else:
            out.append(None)
    return out


def _clean_profiles(raw):
    """Perfiles de Directo {id, name, icon, actions}. Los anteriores a 0.1.4 no traen id ni icono: se les da."""
    out, seen = [], set()
    for i, p in enumerate((raw if isinstance(raw, list) else [])[:100]):
        name = str(p.get("name", "")).strip()[:12] if isinstance(p, dict) else ""
        if not name:
            continue
        pid, n = _clean_id(p.get("id")), i + 1
        while not pid or pid in seen:
            pid, n = f"p{n}", n + 1
        seen.add(pid)
        icon = re.sub(r"[^a-z0-9-]", "", str(p.get("icon", "")).lower())[:30] or "sliders-horizontal"
        out.append({"id": pid, "name": name, "icon": icon, "actions": _clean_actions(p.get("actions"))})
    return out


def normalize_studio(d):
    """Devuelve una configuración válida (descarta lo que no encaja) sin lanzar excepciones."""
    d = d if isinstance(d, dict) else {}
    out = json.loads(json.dumps(DEFAULT_STUDIO))
    out["mode"] = d.get("mode") if d.get("mode") in ("direct", "smart", "modes") else "direct"
    out["trigger"] = d.get("trigger") if d.get("trigger") in TRIGGER_VK else "shift"
    out["led_mode"] = _int(d.get("led_mode"), 0, 255, 1)
    out["flashed"] = str(d.get("flashed", ""))[:2048]  # firma completa de lo último escrito en el teclado
    out.pop("applied", None)
    out["library"] = _clean_library(d.get("library"))
    out["modes"] = _clean_modes(d.get("modes"), {m["id"] for m in out["library"]})
    out["profiles"] = _clean_profiles(d.get("profiles"))
    ids = {p["id"] for p in out["profiles"]}
    active_profile = _clean_id(d.get("active_profile")) if isinstance(d.get("active_profile"), str) else ""
    out["active_profile"] = active_profile if active_profile in ids else None
    slots = d.get("direct_slots") if isinstance(d.get("direct_slots"), list) else []
    out["direct_slots"] = []   # tres huecos del carril de Directo: vacío o el id de un perfil, sin repetir
    for i in range(DIRECT_SLOTS):
        pid = _clean_id(slots[i]) if i < len(slots) and isinstance(slots[i], str) else ""
        out["direct_slots"].append(pid if pid in ids and pid not in out["direct_slots"] else None)
    o = d.get("obs") if isinstance(d.get("obs"), dict) else {}
    out["obs"] = {"host": str(o.get("host", "127.0.0.1"))[:100] or "127.0.0.1",
                  "port": _int(o.get("port"), 1, 65535, 4455), "password": str(o.get("password", ""))[:200]}
    layers, seen = [], set()
    for L in (d.get("layers") if isinstance(d.get("layers"), list) else [])[:30]:
        if not isinstance(L, dict):
            continue
        lid = re.sub(r"[^a-z0-9_-]", "", str(L.get("id", "")).lower())[:40]
        if not lid or lid in seen:
            continue
        seen.add(lid)
        exes = [str(e).strip().lower()[:80] for e in (L.get("exes") if isinstance(L.get("exes"), list) else [])[:10]]
        acts = {}
        for slot, a in (L.get("actions") if isinstance(L.get("actions"), dict) else {}).items():
            c = _clean_action(a)
            if slot in SLOTS and c:
                acts[slot] = c
        layers.append({"id": lid, "name": str(L.get("name", lid))[:40] or lid,
                       "exes": [e for e in exes if e], "actions": acts})
    base = next((L for L in layers if L["id"] == "base"), None)
    if base is None:
        base = {"id": "base", "name": "Base", "exes": [], "actions": {}}
    base["exes"] = []
    out["layers"] = [base] + [L for L in layers if L["id"] != "base"]
    # Recupera configuraciones Spotify creadas antes de separar su sesión de audio.
    for group in out["layers"][1:] + [m for m in out["modes"] if m] + out["library"]:
        if group["name"].strip().casefold() == "spotify" or "spotify.exe" in group.get("exes", []):
            for action in group["actions"].values():
                if action["type"] == "media" and action["code"] in (0xE9, 0xEA, 0xE2):
                    action.update(type="app_volume", target="spotify.exe")
    return out


def load_studio(path=STUDIO_FILE):
    try:
        return normalize_studio(json.loads(Path(path).read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return normalize_studio({})


def save_studio(data, path=STUDIO_FILE):
    clean = normalize_studio(data)
    tmp = Path(str(path) + ".tmp")
    tmp.write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)
    return clean


def resolve(studio, slot, exe, trigger_held, active_mode=None):
    """Decide qué acción corresponde a (botón, app activa, tecla de activación, modo activo).
    Devuelve (acción, origen): id de la capa de la app, «mode:N» o «base»."""
    layers = studio["layers"]
    if trigger_held:
        exe = (exe or "").lower()
        for L in layers[1:]:
            if exe and exe in L["exes"]:
                a = L["actions"].get(slot)
                if a:
                    return a, L["id"]
                break  # capa de la app sin acción en este botón → cae al modo activo / Directo
    if active_mode is not None:
        m = (studio.get("modes") or [None] * MODE_SLOTS)[active_mode]
        if m and m["actions"].get(slot):
            return m["actions"][slot], f"mode:{active_mode}"
    return layers[0]["actions"].get(slot), "base"


def layer_for_exe(studio, exe):
    exe = (exe or "").lower()
    for L in studio["layers"][1:]:
        if exe and exe in L["exes"]:
            return L["id"]
    return "base"


# ----------------------------------------------------------------------------- tablas HID → VK
def _build_hid_vk():
    t = {}
    for i in range(26):
        t[0x04 + i] = 0x41 + i
    for i in range(9):
        t[0x1E + i] = 0x31 + i
    t[0x27] = 0x30
    for i in range(12):
        t[0x3A + i] = 0x70 + i      # F1–F12
        t[0x68 + i] = 0x7C + i      # F13–F24
    t.update({0x28: 0x0D, 0x29: 0x1B, 0x2A: 0x08, 0x2B: 0x09, 0x2C: 0x20, 0x4C: 0x2E, 0x49: 0x2D, 0x4A: 0x24,
              0x4D: 0x23, 0x4B: 0x21, 0x4E: 0x22, 0x4F: 0x27, 0x50: 0x25, 0x51: 0x28, 0x52: 0x26, 0x46: 0x2C,
              0x39: 0x14, 0x47: 0x91, 0x48: 0x13, 0x53: 0x90, 0x2D: 0xBD, 0x2E: 0xBB, 0x2F: 0xDB, 0x30: 0xDD,
              0x31: 0xDC, 0x33: 0xBA, 0x34: 0xDE, 0x35: 0xC0, 0x36: 0xBC, 0x37: 0xBE, 0x38: 0xBF})
    return t


HID_TO_VK = _build_hid_vk()
MEDIA_VK = {0xE9: 0xAF, 0xEA: 0xAE, 0xE2: 0xAD, 0xCD: 0xB3, 0xB5: 0xB0, 0xB6: 0xB1}
VK_TO_HID = {vk: hid for hid, vk in HID_TO_VK.items()}
MODVK = {0x10: 2, 0xA0: 2, 0xA1: 2, 0x11: 1, 0xA2: 1, 0xA3: 1, 0x12: 4, 0xA4: 4, 0xA5: 4, 0x5B: 8, 0x5C: 8}
CAPTURE_TIMEOUT = 20.0  # seguridad: la captura traga TODAS las teclas; jamás debe quedar activa si la interfaz falla
EXTENDED_VK = {0x2E, 0x2D, 0x24, 0x23, 0x21, 0x22, 0x27, 0x25, 0x28, 0x26, 0x5B}


class KeyCapture:
    """Registro de pulsaciones para «Grabar»: el hook las traga y la interfaz las lee por /api/record."""

    def __init__(self):
        self.events = []

    def feed(self, vk, up):
        ev = {"id": vk, "up": bool(up)}
        if vk in MODVK:
            ev["mod"] = MODVK[vk]
        elif vk in VK_TO_HID:
            ev["hid"] = VK_TO_HID[vk]
        else:
            ev["unknown"] = vk
        self.events.append(ev)


# ----------------------------------------------------------------------------- Windows (ctypes)
if IS_WIN:
    import ctypes
    from ctypes import wintypes as wt

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    ULONG_PTR = ctypes.c_size_t
    LRESULT = ctypes.c_ssize_t

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [("wVk", wt.WORD), ("wScan", wt.WORD), ("dwFlags", wt.DWORD), ("time", wt.DWORD), ("dwExtraInfo", ULONG_PTR)]

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [("dx", wt.LONG), ("dy", wt.LONG), ("mouseData", wt.DWORD), ("dwFlags", wt.DWORD),
                    ("time", wt.DWORD), ("dwExtraInfo", ULONG_PTR)]

    class _INPUTUNION(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT)]

    class INPUT(ctypes.Structure):
        _fields_ = [("type", wt.DWORD), ("u", _INPUTUNION)]

    class KBDLLHOOKSTRUCT(ctypes.Structure):
        _fields_ = [("vkCode", wt.DWORD), ("scanCode", wt.DWORD), ("flags", wt.DWORD), ("time", wt.DWORD), ("dwExtraInfo", ULONG_PTR)]

    HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, ctypes.c_size_t, ctypes.c_ssize_t)
    user32.SendInput.argtypes = (wt.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
    user32.SetWindowsHookExW.argtypes = (ctypes.c_int, HOOKPROC, wt.HINSTANCE, wt.DWORD)
    user32.SetWindowsHookExW.restype = ctypes.c_void_p
    user32.CallNextHookEx.argtypes = (ctypes.c_void_p, ctypes.c_int, ctypes.c_size_t, ctypes.c_ssize_t)
    user32.CallNextHookEx.restype = LRESULT
    user32.UnhookWindowsHookEx.argtypes = (ctypes.c_void_p,)
    user32.GetForegroundWindow.restype = ctypes.c_void_p
    user32.GetWindowThreadProcessId.argtypes = (ctypes.c_void_p, ctypes.POINTER(wt.DWORD))
    user32.IsWindowVisible.argtypes = (ctypes.c_void_p,)
    user32.GetWindowTextLengthW.argtypes = (ctypes.c_void_p,)
    user32.GetWindowTextW.argtypes = (ctypes.c_void_p, wt.LPWSTR, ctypes.c_int)
    user32.PostThreadMessageW.argtypes = (wt.DWORD, wt.UINT, ctypes.c_size_t, ctypes.c_ssize_t)
    kernel32.OpenProcess.argtypes = (wt.DWORD, wt.BOOL, wt.DWORD)
    kernel32.OpenProcess.restype = ctypes.c_void_p
    kernel32.CloseHandle.argtypes = (ctypes.c_void_p,)
    kernel32.QueryFullProcessImageNameW.argtypes = (ctypes.c_void_p, wt.DWORD, wt.LPWSTR, ctypes.POINTER(wt.DWORD))
    kernel32.GetModuleHandleW.argtypes = (wt.LPCWSTR,)
    kernel32.GetModuleHandleW.restype = wt.HINSTANCE

    def _send(inputs):
        arr = (INPUT * len(inputs))(*inputs)
        user32.SendInput(len(inputs), arr, ctypes.sizeof(INPUT))

    def _kb(vk, up=False):
        flags = (0x0002 if up else 0) | (0x0001 if vk in EXTENDED_VK else 0)
        return INPUT(1, _INPUTUNION(ki=KEYBDINPUT(vk, 0, flags, 0, 0)))

    def _ms(flags, data=0):
        return INPUT(0, _INPUTUNION(mi=MOUSEINPUT(0, 0, data & 0xFFFFFFFF, flags, 0, 0)))

    def key_down(vk):
        _send([_kb(vk)])

    def key_up(vk):
        _send([_kb(vk, True)])

    def run_keyboard(mod, hid):
        vks = [vk for bit, vk in MOD_VK if mod & bit]
        main = HID_TO_VK.get(hid)
        if main:
            vks.append(main)
        if not vks:
            return
        _send([_kb(v) for v in vks])
        time.sleep(0.012)
        _send([_kb(v, True) for v in reversed(vks)])

    def run_media(code, speed):
        vk = MEDIA_VK.get(code)
        count = max(1, speed) if vk else 0
        for i in range(count):
            _send([_kb(vk), _kb(vk, True)])
            # Evita que pulsaciones consecutivas lleguen como una sola ráfaga
            # a los componentes que procesan las teclas multimedia de Windows.
            if i + 1 < count:
                time.sleep(0.025)

    def adjust_system_volume(code, speed):
        """Ajusta el volumen maestro enviando teclas multimedia nativas de Windows (2% por pulsacion).
        Garantiza respuesta instantanea, visor nativo de Windows (OSD) y cero colisiones."""
        run_media(code, 2)  # 4 puntos con las teclas multimedia de Windows

    def list_audio_apps():
        import comtypes
        from psutil import Error as ProcessError
        from pycaw.pycaw import AudioUtilities
        comtypes.CoInitialize()
        try:
            names = set()
            for session in AudioUtilities.GetAllSessions():
                try:
                    process = session.Process
                    if process:
                        names.add(process.name().lower())
                except (OSError, ProcessError):
                    continue  # El proceso pudo cerrarse mientras se enumeraba.
            return sorted(names)
        finally:
            comtypes.CoUninitialize()

    def adjust_spotify_volume(code, step, target="spotify.exe"):
        """Controla todas las sesiones de Spotify sin cambiar el volumen maestro."""
        import comtypes
        from pycaw.pycaw import AudioUtilities
        comtypes.CoInitialize()
        try:
            controls = []
            for session in AudioUtilities.GetAllSessions():
                process = session.Process
                if process and process.name().lower() == target.lower():
                    controls.append(session.SimpleAudioVolume)
            if not controls:
                raise RuntimeError(f"{target} no tiene una sesión de audio activa.")
            mute = not controls[0].GetMute() if code == 0xE2 else None
            for control in controls:
                if mute is not None:
                    control.SetMute(mute, None)
                else:
                    current = round(control.GetMasterVolume() * 100)
                    level = max(0, min(100, current + (step if code == 0xE9 else -step)))
                    control.SetMasterVolume(level / 100.0, None)
        finally:
            comtypes.CoUninitialize()

    _MOUSE_FLAGS = {1: (0x0002, 0x0004, 0), 2: (0x0008, 0x0010, 0), 4: (0x0020, 0x0040, 0),
                    8: (0x0080, 0x0100, 1), 16: (0x0080, 0x0100, 2)}

    def run_mouse(mod, buttons, wheel, speed):
        vks = [vk for bit, vk in MOD_VK if mod & bit]
        if vks:
            _send([_kb(v) for v in vks])
            time.sleep(0.012)
        if buttons:
            for bit, (down, up, data) in _MOUSE_FLAGS.items():
                if buttons & bit:
                    _send([_ms(down, data), _ms(up, data)])
        if wheel:
            _send([_ms(0x0800, wheel * max(1, speed) * 120)])
        if vks:
            _send([_kb(v, True) for v in reversed(vks)])

    def _exe_of(hwnd):
        pid = wt.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        h = kernel32.OpenProcess(0x1000, False, pid.value)
        if not h:
            return ""
        try:
            buf = ctypes.create_unicode_buffer(520)
            n = wt.DWORD(520)
            if kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n)):
                return os.path.basename(buf.value).lower()
        finally:
            kernel32.CloseHandle(h)
        return ""

    def foreground_exe():
        hwnd = user32.GetForegroundWindow()
        return _exe_of(hwnd) if hwnd else ""

    def list_windows():
        found, seen = [], set()
        proc = ctypes.WINFUNCTYPE(wt.BOOL, ctypes.c_void_p, ctypes.c_ssize_t)

        @proc
        def cb(hwnd, _):
            if user32.IsWindowVisible(hwnd):
                n = user32.GetWindowTextLengthW(hwnd)
                if n:
                    buf = ctypes.create_unicode_buffer(n + 1)
                    user32.GetWindowTextW(hwnd, buf, n + 1)
                    exe = _exe_of(hwnd)
                    if exe and exe not in seen:
                        seen.add(exe)
                        found.append({"exe": exe, "title": buf.value[:80]})
            return True

        user32.EnumWindows(cb, 0)
        return found

    class KeyHook:
        """Hook de teclado de bajo nivel en su propio hilo. Solo reacciona a F13–F18 y a la tecla de activación."""

        def __init__(self, on_ghost, accept_injected=False):
            self.on_ghost = on_ghost
            self.accept_injected = accept_injected
            self.trigger = "shift"
            self.capture = None
            self.ghost_slots = set(GHOST_VK.values())
            self.phys = {"shift": False, "ctrl": False, "alt": False}
            self.tid = 0
            self.hhook = None
            self._ready = threading.Event()
            self._proc = HOOKPROC(self._callback)  # referencia viva: si se recolecta, Windows se cuelga
            self._thread = threading.Thread(target=self._run, daemon=True, name="studio-hook")

        def _callback(self, n, w, l):
            if n == 0:
                k = ctypes.cast(l, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                if self.accept_injected or not (k.flags & 0x10):
                    vk, up = k.vkCode, bool(k.flags & 0x80)
                    cap = self.capture
                    if cap is not None:
                        cap.feed(vk, up)
                        return 1  # grabando: ni Windows ni las apps ven la tecla (Alt+Tab, Win…)
                    if vk in GHOST_VK and GHOST_VK[vk] in self.ghost_slots:
                        if not up:
                            chord = chord_held(self.phys)   # Ctrl+Shift: cambio de modo
                            self.on_ghost(GHOST_VK[vk], self.phys[self.trigger], chord)
                        return 1  # se traga: ninguna app ve F13–F18
                    for name, vks in TRIGGER_VKS.items():
                        if vk in vks:
                            self.phys[name] = not up
                            break
            return user32.CallNextHookEx(None, n, w, l)

        def _run(self):
            self.tid = kernel32.GetCurrentThreadId()
            self.hhook = user32.SetWindowsHookExW(13, self._proc, kernel32.GetModuleHandleW(None), 0)
            self._ready.set()
            if not self.hhook:
                return
            msg = wt.MSG()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                pass
            user32.UnhookWindowsHookEx(self.hhook)

        def start(self):
            self._thread.start()
            self._ready.wait(2)
            return bool(self.hhook)

        def stop(self):
            if self.tid:
                user32.PostThreadMessageW(self.tid, 0x0012, 0, 0)  # WM_QUIT
else:
    def foreground_exe():
        return ""

    def list_windows():
        return []

    def list_audio_apps():
        return []


# ----------------------------------------------------------------------------- OBS WebSocket v5
class ObsClient:
    """Cliente mínimo de obs-websocket 5.x (OBS 28+) sin dependencias: handshake HTTP + tramas de texto."""

    def __init__(self):
        self.cfg = DEFAULT_STUDIO["obs"]
        self.sock = None
        self.rf = None
        self.rid = 0
        self.lock = threading.Lock()

    def configure(self, cfg):
        if cfg != self.cfg:
            self.close()
        self.cfg = cfg

    def close(self):
        for o in (self.rf, self.sock):
            try:
                o and o.close()
            except OSError:
                pass
        self.sock = self.rf = None

    def _send(self, obj):
        data = json.dumps(obj).encode("utf-8")
        n = len(data)
        hdr = bytearray([0x81])
        if n < 126:
            hdr.append(0x80 | n)
        elif n < 65536:
            hdr += bytes([0x80 | 126]) + struct.pack(">H", n)
        else:
            hdr += bytes([0x80 | 127]) + struct.pack(">Q", n)
        mask = os.urandom(4)
        self.sock.sendall(bytes(hdr) + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def _read(self, n):
        buf = self.rf.read(n)
        if len(buf) < n:
            raise ConnectionError("OBS cerró la conexión")
        return buf

    def _recv(self):
        while True:
            b1, b2 = self._read(2)
            op, ln = b1 & 0x0F, b2 & 0x7F
            if ln == 126:
                ln = struct.unpack(">H", self._read(2))[0]
            elif ln == 127:
                ln = struct.unpack(">Q", self._read(8))[0]
            payload = self._read(ln)
            if op == 8:
                raise ConnectionError("OBS cerró la conexión")
            if op == 9:  # ping → pong
                mask = os.urandom(4)
                self.sock.sendall(bytes([0x8A, 0x80 | len(payload)]) + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(payload)))
                continue
            if op == 1:
                return json.loads(payload.decode("utf-8"))

    def connect(self):
        c = self.cfg
        self.sock = socket.create_connection((c["host"], c["port"]), timeout=2)
        self.sock.settimeout(3)
        self.rf = self.sock.makefile("rb")
        key = base64.b64encode(os.urandom(16)).decode()
        self.sock.sendall((f"GET / HTTP/1.1\r\nHost: {c['host']}:{c['port']}\r\nUpgrade: websocket\r\n"
                           f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n"
                           f"Sec-WebSocket-Protocol: obswebsocket.json\r\n\r\n").encode())
        status = self.rf.readline()
        if b" 101 " not in status:
            raise ConnectionError("OBS no acepta WebSocket en ese puerto")
        while self.rf.readline() not in (b"\r\n", b""):
            pass
        hello = self._recv()
        ident = {"rpcVersion": 1}
        auth = hello.get("d", {}).get("authentication")
        if auth:
            secret = base64.b64encode(hashlib.sha256((c["password"] + auth["salt"]).encode()).digest()).decode()
            ident["authentication"] = base64.b64encode(hashlib.sha256((secret + auth["challenge"]).encode()).digest()).decode()
        self._send({"op": 1, "d": ident})
        if self._recv().get("op") != 2:
            raise ConnectionError("OBS rechazó la identificación (¿contraseña?)")

    def req(self, rtype, data=None):
        self.rid += 1
        rid = str(self.rid)
        self._send({"op": 6, "d": {"requestType": rtype, "requestId": rid, "requestData": data or {}}})
        while True:
            m = self._recv()
            if m.get("op") == 7 and m["d"].get("requestId") == rid:
                st = m["d"]["requestStatus"]
                if not st.get("result"):
                    raise RuntimeError(f"OBS: {st.get('comment') or st.get('code')}")
                return m["d"].get("responseData") or {}

    def run(self, a):
        with self.lock:
            for attempt in (0, 1):
                try:
                    if not self.sock:
                        self.connect()
                    return self._do(a)
                except (OSError, ConnectionError):
                    self.close()
                    if attempt:
                        raise

    def _do(self, a):
        op, target, step = a["op"], a.get("target", ""), a.get("speed", 1)
        if op in ("next_scene", "prev_scene"):
            r = self.req("GetSceneList")
            names = [s["sceneName"] for s in sorted(r["scenes"], key=lambda s: -s["sceneIndex"])]  # orden de la lista de OBS
            cur = r["currentProgramSceneName"]
            i = names.index(cur) if cur in names else 0
            self.req("SetCurrentProgramScene", {"sceneName": names[(i + (1 if op == "next_scene" else -1)) % len(names)]})
        elif op == "scene":
            self.req("SetCurrentProgramScene", {"sceneName": target})
        elif op == "toggle_source":
            scene = self.req("GetCurrentProgramScene")["currentProgramSceneName"]
            sid = self.req("GetSceneItemId", {"sceneName": scene, "sourceName": target})["sceneItemId"]
            on = self.req("GetSceneItemEnabled", {"sceneName": scene, "sceneItemId": sid})["sceneItemEnabled"]
            self.req("SetSceneItemEnabled", {"sceneName": scene, "sceneItemId": sid, "sceneItemEnabled": not on})
        elif op == "toggle_mute":
            self.req("ToggleInputMute", {"inputName": target})
        elif op in ("volume_up", "volume_down"):
            db = self.req("GetInputVolume", {"inputName": target})["inputVolumeDb"]
            db = max(-100.0, min(26.0, db + (4 if op == "volume_up" else -4)))
            self.req("SetInputVolume", {"inputName": target, "inputVolumeDb": db})
        elif op == "toggle_record":
            self.req("ToggleRecord")
        elif op == "toggle_stream":
            self.req("ToggleStream")


# ----------------------------------------------------------------------------- motor
class StudioEngine:
    def __init__(self, simulate=False, accept_injected=False, path=STUDIO_FILE):
        self.path = path
        self.simulate = simulate
        self.accept_injected = accept_injected
        self.studio = load_studio(path)
        self.hook = None
        self.q = queue.Queue()
        self.worker = None
        self.obs = ObsClient()
        self.obs.configure(self.studio["obs"])
        self.foreground = foreground_exe
        self.executed = []                 # (acción, capa) — solo en simulación
        self.last = None
        self.error = ""
        self.events = deque(maxlen=20)
        self.temp_hook = False
        self.cap_timer = None
        self.mode_light = None             # conexión USB instalada por app.py
        self.active_mode = None            # índice 0–2 del modo activo; None = Directo (no se guarda: al arrancar, Directo)

    # -- ciclo de vida
    def apply(self, studio, persist=True):
        self.studio = save_studio(studio, self.path) if persist else normalize_studio(studio)
        self.obs.configure(self.studio["obs"])
        if self.active_mode is not None and not self.studio["modes"][self.active_mode]:
            self.active_mode = None        # el modo activo se quitó desde la interfaz
        self.start()                       # el docker y la app son uno: el motor siempre está activo
        return self.studio

    def set_mode(self, index, physical=False):
        """Ctrl+Shift+N: activa el modo N; repetirlo (o un hueco vacío) vuelve a Directo. Devuelve el índice activo o None."""
        m = self.studio["modes"][index] if 0 <= index < MODE_SLOTS else None
        if not m:
            return self.active_mode
        self.active_mode = None if self.active_mode == index else index
        # El cambio de modo solo afecta al motor. Escribir la iluminación aquí
        # puede dejar la rueda inconsistente hasta reconectar el macropad.
        if not self.simulate:
            try:
                from volume_overlay import show_message
                if self.active_mode is None:
                    show_message("target", "Directo")
                else:
                    show_message(m["icon"], m["name"], f"Ctrl+Shift+{index + 1}")
            except Exception:
                pass
        return self.active_mode

    def start(self):
        if not IS_WIN:
            self.error = "El modo inteligente solo está disponible en Windows."
            return False
        if self.hook is not None and self.temp_hook:  # había un hook solo para grabar: pasa a ser el real
            self.stop_capture()
            self.stop()
        if self.hook is None:
            hook = KeyHook(self._on_ghost, self.accept_injected)
            if not hook.start():
                self.error = "Windows no permitió instalar el hook de teclado."
                return False
            self.hook = hook
            self.worker = threading.Thread(target=self._loop, daemon=True, name="studio-worker")
            self.worker.start()
        self.hook.trigger = self.studio["trigger"]
        self.hook.ghost_slots = set(GHOST_VK.values())
        self.error = ""
        return True

    def stop(self):
        if self.mode_light is not None:
            self.mode_light.close()
        if self.hook:
            self.hook.stop()
            self.hook = None
            self.temp_hook = False
            self.q.put(None)
            self.worker = None

    # -- eventos
    def _on_ghost(self, slot, trigger_held, chord=False):  # hilo del hook: lo mínimo
        self.q.put((slot, trigger_held, chord))

    def _loop(self):
        while True:
            item = self.q.get()
            if item is None:
                return
            try:
                self.handle(*item)
            except Exception as exc:  # un fallo de una acción no debe matar el motor
                self.error = f"{type(exc).__name__}: {exc}"

    def handle(self, slot, trigger_held, chord=False):
        if chord and slot in MODE_KEYS:
            # Ctrl y Shift siguen pulsados y la tecla fantasma no llegó a Windows: sin esta pulsación neutra,
            # al soltarlos Windows podría tomarlo por un atajo de Ctrl/Shift o abrir un menú.
            if IS_WIN and not self.simulate:
                key_down(0xFF)
                key_up(0xFF)
            self.set_mode(MODE_KEYS.index(slot), physical=True)
            self.last = {"slot": slot, "exe": "", "layer": "mode-switch", "trigger": False, "action": "mode",
                         "at": time.time()}
            return
        exe = self.foreground()
        action, layer = resolve(self.studio, slot, exe, trigger_held, self.active_mode)
        self.last = {"slot": slot, "exe": exe, "layer": layer, "trigger": trigger_held,
                     "action": action and action.get("type"), "at": time.time()}
        if action:
            self.perform(action, self.studio["trigger"] if trigger_held else None)

    def perform(self, a, release=None):
        if self.simulate:
            self.executed.append((a, self.last and self.last["layer"]))
            return
        t = a["type"]
        if t == "obs":
            self.obs.run(a)
            return
        # Con Shift/Ctrl/Alt físico pulsado, la app vería Shift+acción: se suelta y se restaura al terminar
        vk = TRIGGER_VK.get(release) if IS_WIN else None
        if vk:
            key_up(vk)
        try:
            if t == "keyboard":
                run_keyboard(a["mod"], a["code"])
            elif t == "app_volume":
                adjust_spotify_volume(a["code"], 4, a.get("target", "spotify.exe"))
            elif t == "media":
                if a["code"] in (0xE9, 0xEA):
                    adjust_system_volume(a["code"], a["speed"])
                else:
                    run_media(a["code"], a["speed"])
            elif t == "mouse":
                run_mouse(a["mod"], a["code"], a["wheel"], a["speed"])
        finally:
            if vk and self.hook and self.hook.phys.get(release):
                key_down(vk)

    # -- grabación nativa (teclado completo, incluidos Alt+Tab y Win; solo Ctrl+Alt+Supr es intocable)
    def start_capture(self):
        if not IS_WIN:
            return False
        if self.hook is None:
            hook = KeyHook(lambda *_: None, self.accept_injected)
            if not hook.start():
                return False
            self.hook, self.temp_hook = hook, True
        self.hook.capture = KeyCapture()
        if self.cap_timer:
            self.cap_timer.cancel()
        self.cap_timer = threading.Timer(CAPTURE_TIMEOUT, self.stop_capture)
        self.cap_timer.daemon = True
        self.cap_timer.start()
        return True

    def capture_events(self, since=0):
        cap = self.hook.capture if self.hook else None
        return {"active": cap is not None, "events": cap.events[since:] if cap else [], "next": (len(cap.events) if cap else since)}

    def stop_capture(self):
        if self.cap_timer:
            self.cap_timer.cancel()
            self.cap_timer = None
        if self.hook:
            self.hook.capture = None
            if self.temp_hook:
                self.stop()

    def run_now(self, action, delay=0.0):
        """Ejecuta una acción a petición de la interfaz («Probar») tras una cuenta atrás."""
        a = _clean_action(action)
        if not a:
            return False

        def go():
            time.sleep(delay)
            try:
                self.perform(a)
            except Exception as exc:
                self.error = f"{type(exc).__name__}: {exc}"

        threading.Thread(target=go, daemon=True).start()
        return True

    def status(self):
        exe = self.foreground()
        return {"platform_ok": IS_WIN, "running": self.hook is not None, "mode": self.studio["mode"],
                "trigger": self.studio["trigger"], "active_exe": exe,
                "active_layer": layer_for_exe(self.studio, exe),
                "active_mode": -1 if self.active_mode is None else self.active_mode,
                "last": self.last, "error": self.error}


ENGINE = StudioEngine()
