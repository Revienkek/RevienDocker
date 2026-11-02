/* RevienDocker — interfaz. Sin dependencias. El estado vive en `S` y se guarda en localStorage y (si hay servidor) en studio.json. */
(() => {
const $ = id => document.getElementById(id);
const MAX_KEYS = 3;
const MOD_BITS = [
  { name: "Ctrl",  bit: 1, dom: ["ControlLeft", "ControlRight"] },
  { name: "Shift", bit: 2, dom: ["ShiftLeft", "ShiftRight"] },
  { name: "Alt",   bit: 4, dom: ["AltLeft", "AltRight"] },
  { name: "Win",   bit: 8, dom: ["MetaLeft", "MetaRight"] }
];

// ---------- Catálogo de teclas (HID Usage 0x07), indexado también por KeyboardEvent.code ----------
const KEYS = [], DOM_TO_HID = {}, SHORT_OF = {};
function addKey(dom, code, short, group, label) {
  KEYS.push({ code, short, group, label: label || short });
  DOM_TO_HID[dom] = code; SHORT_OF[code] = short;
}
for (let i = 0; i < 26; i++) { const ch = String.fromCharCode(65 + i); addKey("Key" + ch, 0x04 + i, ch, "Letras"); }
for (let i = 1; i <= 9; i++) addKey("Digit" + i, 0x1D + i, String(i), "Números");
addKey("Digit0", 0x27, "0", "Números");
for (let i = 1; i <= 12; i++) addKey("F" + i, 0x39 + i, "F" + i, "F1 – F12");
for (let i = 13; i <= 24; i++) addKey("F" + i, 0x68 + (i - 13), "F" + i, "F13 – F24", i <= 18 ? `F${i} (Fantasma ${i - 12})` : null);
[["Enter", 0x28, "Enter"], ["Escape", 0x29, "Esc"], ["Backspace", 0x2A, "Backspace"], ["Tab", 0x2B, "Tab"],
 ["Space", 0x2C, "Space"], ["Delete", 0x4C, "Supr"], ["Insert", 0x49, "Ins"], ["Home", 0x4A, "Inicio"],
 ["End", 0x4D, "Fin"], ["PageUp", 0x4B, "RePág"], ["PageDown", 0x4E, "AvPág"], ["ArrowRight", 0x4F, "→"],
 ["ArrowLeft", 0x50, "←"], ["ArrowDown", 0x51, "↓"], ["ArrowUp", 0x52, "↑"], ["PrintScreen", 0x46, "ImpPant"],
 ["CapsLock", 0x39, "Bloq Mayús"], ["ScrollLock", 0x47, "BloqDesp"], ["Pause", 0x48, "Pausa"], ["NumLock", 0x53, "BloqNum"]
].forEach(([d, c, s]) => addKey(d, c, s, "Edición y navegación"));
[["Minus", 0x2D, "-"], ["Equal", 0x2E, "="], ["BracketLeft", 0x2F, "["], ["BracketRight", 0x30, "]"],
 ["Backslash", 0x31, "\\"], ["Semicolon", 0x33, ";"], ["Quote", 0x34, "'"], ["Backquote", 0x35, "`"],
 ["Comma", 0x36, ","], ["Period", 0x37, "."], ["Slash", 0x38, "/"]
].forEach(([d, c, s]) => addKey(d, c, s, "Símbolos"));
const kc = dom => DOM_TO_HID[dom];

// ---------- Ratón, multimedia y OBS ----------
const MOUSE_BTNS = [
  { bit: 1,  short: "Clic izq.",    label: "Botón izquierdo" },
  { bit: 2,  short: "Clic der.",    label: "Botón derecho" },
  { bit: 4,  short: "Clic central", label: "Botón central (rueda)" },
  { bit: 8,  short: "Atrás",        label: "Botón Atrás (lateral 1)" },
  { bit: 16, short: "Adelante",     label: "Botón Adelante (lateral 2)" }
];
const MOUSE_SHORT = Object.fromEntries(MOUSE_BTNS.map(b => [b.bit, b.short]));
const MEDIA = [
  { code: 0xE9, short: "Vol +",      label: "Subir volumen" },
  { code: 0xEA, short: "Vol -",      label: "Bajar volumen" },
  { code: 0xE2, short: "Mute",       label: "Silenciar" },
  { code: 0xCD, short: "Play/Pausa", label: "Play / Pausa" },
  { code: 0xB5, short: "Siguiente",  label: "Pista siguiente" },
  { code: 0xB6, short: "Anterior",   label: "Pista anterior" }
];
const MEDIA_SHORT = Object.fromEntries(MEDIA.map(m => [m.code, m.short]));
const OBS_OPS = [
  { op: "next_scene",    label: "Escena siguiente",        short: "Escena ▶" },
  { op: "prev_scene",    label: "Escena anterior",         short: "Escena ◀" },
  { op: "scene",         label: "Ir a una escena…",        short: t => "Escena: " + t, needs: "Nombre de la escena", def: "" },
  { op: "toggle_source", label: "Mostrar / ocultar fuente…", short: t => "Fuente: " + t, needs: "Fuente de la escena actual (ej. Fondo negro)", def: "Fondo negro" },
  { op: "toggle_mute",   label: "Silenciar micro…",        short: t => "Mute " + t, needs: "Entrada de audio (ej. Mic/Aux)", def: "Mic/Aux" },
  { op: "volume_up",     label: "Subir volumen…",          short: t => "Vol+ " + t, needs: "Entrada de audio (ej. Mic/Aux)", def: "Mic/Aux", speed: true },
  { op: "volume_down",   label: "Bajar volumen…",          short: t => "Vol- " + t, needs: "Entrada de audio (ej. Mic/Aux)", def: "Mic/Aux", speed: true },
  { op: "toggle_record", label: "Iniciar / parar grabación", short: "Grabar ⏺" },
  { op: "toggle_stream", label: "Iniciar / parar directo", short: "Directo 📡" }
];
const OBS_BY_OP = Object.fromEntries(OBS_OPS.map(o => [o.op, o]));
const SPEEDS = [[1, "Fino"], [2, "Normal"], [3, "Rápido"], [5, "Turbo"]];

// ---------- Acciones: { type, mod, code, wheel (-1/0/1), speed [, op, target] } ----------
const K  = (mod, code) => ({ type: "keyboard", mod, code, wheel: 0, speed: 1 });
const M  = (code, speed = 1) => ({ type: "media", mod: 0, code, wheel: 0, speed });
const Ms = (mod, btn, wheel = 0, speed = 1) => ({ type: "mouse", mod, code: btn, wheel, speed });
const O  = (op, target = "", speed = 1) => ({ type: "obs", mod: 0, code: 0, wheel: 0, speed, op, target });
const EMPTY = K(0, 0);
const popcount = m => MOD_BITS.filter(x => m & x.bit).length;
const hasMain = a => a.type === "keyboard" ? !!a.code : a.type === "mouse" ? !!(a.code || a.wheel) : true;
const countOf = a => (a.type === "media" || a.type === "obs") ? 1 : popcount(a.mod) + (hasMain(a) ? 1 : 0);
const speedApplies = a => (a.type === "media" && (a.code === 0xE9 || a.code === 0xEA)) || (a.type === "mouse" && !!a.wheel) ||
  (a.type === "obs" && !!(OBS_BY_OP[a.op] || {}).speed);
const sameAction = (a, b) => !!a && !!b && a.type === b.type && a.mod === b.mod && a.code === b.code && a.wheel === b.wheel && a.op === b.op;
const modsOf = a => (a.type === "media" || a.type === "obs") ? 0 : a.mod;
const speedOf = a => speedApplies(a) ? a.speed : 1;

function describe(a) {
  const mods = MOD_BITS.filter(x => a.mod & x.bit).map(x => x.name);
  let main = "", head = [];
  if (a.type === "keyboard") main = a.code ? SHORT_OF[a.code] : "";
  else if (a.type === "mouse") main = a.wheel ? (a.wheel > 0 ? "Rueda ↑" : "Rueda ↓") : (MOUSE_SHORT[a.code] || "");
  else if (a.type === "media") main = MEDIA_SHORT[a.code] || "";
  else { head = ["OBS"]; const o = OBS_BY_OP[a.op]; main = o ? (typeof o.short === "function" ? o.short(a.target || "…") : o.short) : "?"; }
  return { parts: [...head, ...mods, ...(main ? [main] : [])], speed: speedApplies(a) && a.speed > 1 ? a.speed : 0,
    volumeStep: a.type === "media" && (a.code === 0xE9 || a.code === 0xEA) };
}
const textOf = a => { const d = describe(a); return (d.parts.join(a.type === "obs" ? " · " : "+") + (d.speed ? (d.volumeStep ? ` · ${d.speed}%` : " ×" + d.speed) : "")) || "—"; };
const TYPE_NAME = { keyboard: "Teclado", mouse: "Ratón", media: "Multimedia", obs: "OBS Studio" };
const TARGET_NAME = { KEY_1: "Tecla 1", KEY_2: "Tecla 2", KEY_3: "Tecla 3", KNOB_CCW: "Giro ↺ izquierda", KNOB_CW: "Giro ↻ derecha", KNOB_PRESS: "Pulsación del pomo" };
const SLOT_ORDER = ["KEY_1", "KEY_2", "KEY_3", "KNOB_CCW", "KNOB_PRESS", "KNOB_CW"];
const HW_SLOTS = { KEY_1: 0x01, KEY_2: 0x02, KEY_3: 0x03, KNOB_CCW: 0x0D, KNOB_PRESS: 0x0E, KNOB_CW: 0x0F };
const GHOST = { KEY_1: "F13", KEY_2: "F14", KEY_3: "F15", KNOB_CCW: "F16", KNOB_CW: "F17", KNOB_PRESS: "F18" };
const TRIGGERS = { shift: "Shift", ctrl: "Ctrl", alt: "Alt" };

// ---------- Estado ----------
const defaultBase = () => ({ KEY_1: K(0, kc("F13")), KEY_2: K(0, kc("F14")), KEY_3: K(0, kc("F15")), KNOB_CCW: M(0xEA), KNOB_PRESS: M(0xE2), KNOB_CW: M(0xE9) });
const defaultState = () => ({ mode: "direct", trigger: "shift", led_mode: 1, flashed: "", modes: [null, null, null], profiles: [], obs: { host: "127.0.0.1", port: 4455, password: "" },
  layers: [{ id: "base", name: "Base", exes: [], actions: defaultBase() }] });
const LS_KEY = "botonera.studio.v2";
let S = defaultState();
let layerId = "base", currentTarget = "KEY_1", knobSpeed = 1, modeIdx = 0, liveMode = -1, savedSnap = "";
const API = { ok: false, desktop: false };
let deviceConnected = false;
// Tres capas de edición sobre el mismo dibujo: Directo (base), una app (Inteligente) o un hueco de Modos.
// Las dos últimas heredan de Directo lo que no definen, igual que el motor.
const slotMode = () => S.modes[modeIdx];
const layer = () => S.mode === "modes" ? (slotMode() || { actions: {} }) : (S.layers.find(l => l.id === layerId) || S.layers[0]);
const isApp = () => S.mode === "modes" || layer().id !== "base";
const editable = () => S.mode === "direct" || (S.mode === "smart" ? layerId !== "base" : !!slotMode());
const own = slot => layer().actions[slot];
const shown = slot => own(slot) || (isApp() ? S.layers[0].actions[slot] : undefined);
const cur = () => shown(currentTarget) || EMPTY;

function fixState(s) {
  const d = defaultState();
  s = s && typeof s === "object" ? s : d;
  s.mode = ["direct", "smart", "modes"].includes(s.mode) ? s.mode : "direct";
  s.trigger = TRIGGERS[s.trigger] ? s.trigger : "shift";
  s.led_mode = Number.isInteger(s.led_mode) ? s.led_mode : 1;
  s.flashed = typeof s.flashed === "string" ? s.flashed : "";
  s.modes = [0, 1, 2].map(i => {
    const m = Array.isArray(s.modes) ? s.modes[i] : null;
    return m && typeof m === "object" ? { name: String(m.name || `Modo ${i + 1}`).slice(0, 30), icon: String(m.icon || "sliders-horizontal"),
      actions: m.actions && typeof m.actions === "object" ? m.actions : {} } : null;
  });
  s.profiles = Array.isArray(s.profiles) ? s.profiles.filter(p => p && typeof p.name === "string" && p.actions && typeof p.actions === "object").map(p => ({name: p.name.slice(0, 12), actions: p.actions})) : [];
  s.obs = { ...d.obs, ...(s.obs || {}) };
  s.layers = Array.isArray(s.layers) && s.layers.length ? s.layers : d.layers;
  if (s.layers[0].id !== "base") s.layers.unshift(d.layers[0]);
  s.layers.forEach(l => { l.exes = l.exes || []; l.actions = l.actions || {}; });
  if (!Object.keys(s.layers[0].actions).length) s.layers[0].actions = defaultBase();
  return s;
}

async function api(path, body) {
  const opt = body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json", "X-Studio": "1" }, body: JSON.stringify(body) };
  const r = await fetch(path, opt);
  if (!r.ok) throw new Error(r.status);
  return r.json();
}
let saveTimer = null;
function persist() {
  try { localStorage.setItem(LS_KEY, JSON.stringify(S)); } catch (_) {}
  if (!API.ok) return;
  clearTimeout(saveTimer);
  saveTimer = setTimeout(() => api("/api/config", { studio: S }).then(updateEngineUI).catch(() => {}), 350);
}
const snapOf = () => JSON.stringify({ layers: S.layers, modes: S.modes, trigger: S.trigger });
async function load() {
  let ls = null;
  try { ls = JSON.parse(localStorage.getItem(LS_KEY)); } catch (_) {}
  try {
    const r = await api("/api/config");
    API.ok = true;
    const serverEmpty = !Object.keys(r.studio.layers[0].actions).length && r.studio.layers.length === 1;
    S = fixState(serverEmpty && ls ? ls : r.studio);
    if (serverEmpty && ls) persist();
  } catch (_) { S = fixState(ls); }
  savedSnap = snapOf();
}

// ---------- Utilidades de UI ----------
const hexOf = f => Array.from(f).slice(0, 11).map(x => x.toString(16).padStart(2, "0").toUpperCase()).join(" ");
function logLine(text, color) { if (color === "#fbbf24") toast(text, true); }
let toastTimer = null;
function toast(text, warn) {
  const t = $("toast");
  t.textContent = text; t.classList.toggle("warn", !!warn); t.classList.add("show");
  clearTimeout(toastTimer); toastTimer = setTimeout(() => t.classList.remove("show"), 2000);
}
const setVal = (el, v) => { if (document.activeElement !== el) el.value = v; };
const reduceMotion = () => matchMedia("(prefers-reduced-motion: reduce)").matches;
function swapFx() { if (!reduceMotion()) $("chassis").animate([{ opacity: 0.35 }, { opacity: 1 }], { duration: 140, easing: "cubic-bezier(0.23, 1, 0.32, 1)" }); }
function el(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }

function renderChips(box, a) {
  box.innerHTML = "";
  const d = describe(a);
  if (!d.parts.length) { box.appendChild(el("span", "muted", "Sin asignar")); return; }
  d.parts.forEach((p, i) => {
    if (i) box.appendChild(el("span", "chip-plus", "+"));
    box.appendChild(el("span", "chip", p));
  });
  if (d.speed) box.appendChild(el("span", "chip-x", d.volumeStep ? `Paso ${d.speed}%` : "×" + d.speed));
}
function renderSeg(box, current, onPick, items = SPEEDS.map(([v, n]) => [v, `${n} ×${v}`])) {
  box.innerHTML = "";
  items.forEach(([v, label]) => {
    const b = el("button", v === current ? "active" : "", label);
    b.addEventListener("click", () => onPick(v));
    box.appendChild(b);
  });
}

// ---------- Paquetes ----------
const isWheelVolume = (slot, a) => (slot === "KNOB_CCW" || slot === "KNOB_CW") && a && a.type === "media" && (a.code === 0xE9 || a.code === 0xEA);
// El docker y la app son uno: el teclado solo manda F13–F18 y el motor decide qué hacer (Directo, Inteligente o Modos).
const hwAction = slot => K(0, kc(GHOST[slot]));
// Mismo protocolo que el backend (app.py): cada mensaje son 63 bytes tras el Report ID 0x03.
function msg(...b) { const m = new Uint8Array(63); m.set(b.map(x => x & 0xFF)); return m; }
function slotMessages(slot, a) {
  const id = HW_SLOTS[slot], out = [msg(0xFE, 1, 1, 1)];
  if (a.type === "media") out.push(msg(id, 0x12, a.code & 0xFF, a.code >> 8));
  else if (a.type === "mouse") out.push(msg(id, 0x13, a.code, 0, 0, a.wheel * a.speed, a.mod));
  else out.push(msg(id, 0x11, 1, 0, 0, 0), msg(id, 0x11, 1, 1, a.mod, a.code));
  out.push(msg(0xAA, 0xAA));
  return out;
}

// ---------- Recetas de rueda ----------
const RECIPES = [
  { icon: "volume-2", name: "Volumen", desc: "Sube y baja el volumen del PC; pulsar silencia", ccw: M(0xEA), cw: M(0xE9), press: M(0xE2) },
  { icon: "scroll", name: "Scroll", desc: "Desplaza cualquier página; pulsar = clic central (autoscroll)", ccw: Ms(0, 0, 1), cw: Ms(0, 0, -1), press: Ms(0, 4) },
  { icon: "zoom-in", name: "Zoom", desc: "Ctrl + rueda en navegador, Photoshop, Excel…; pulsar = 100%", ccw: Ms(1, 0, -1), cw: Ms(1, 0, 1), press: K(1, kc("Digit0")) },
  { icon: "panel-top", name: "Pestañas", desc: "Salta entre pestañas; pulsar reabre la cerrada", ccw: K(3, kc("Tab")), cw: K(1, kc("Tab")), press: K(3, kc("KeyT")) },
  { icon: "film", name: "Línea de tiempo", desc: "← → fotograma a fotograma; pulsar = Espacio", ccw: K(0, kc("ArrowLeft")), cw: K(0, kc("ArrowRight")), press: K(0, kc("Space")) },
  { icon: "undo-2", name: "Deshacer / Rehacer", desc: "Viaja por el historial; pulsar = Guardar", ccw: K(1, kc("KeyZ")), cw: K(1, kc("KeyY")), press: K(1, kc("KeyS")) },
  { icon: "skip-forward", name: "Pistas", desc: "Anterior / siguiente; pulsar = Play/Pausa", ccw: M(0xB6), cw: M(0xB5), press: M(0xCD) },
  { icon: "brush", name: "Pincel", desc: "[ y ] en Photoshop, Krita, GIMP…", ccw: K(0, kc("BracketLeft")), cw: K(0, kc("BracketRight")) },
  { icon: "mic", name: "Micro OBS", desc: "Ajusta la entrada Mic/Aux de OBS; pulsar = mute", obs: true,
    ccw: O("volume_down", "Mic/Aux"), cw: O("volume_up", "Mic/Aux"), press: O("toggle_mute", "Mic/Aux") }
];
const withSpeed = (a, s) => ({ ...a, speed: speedApplies(a) ? s : 1 });
const LIB = [["Alt+Tab", 4, "Tab"], ["Win+Tab", 8, "Tab"], ["Alt+F4", 4, "F4"], ["Win+D", 8, "KeyD"], ["Win+L", 8, "KeyL"], ["Win+E", 8, "KeyE"],
  ["Win+V", 8, "KeyV"], ["Win+Shift+S", 10, "KeyS"], ["Ctrl+Alt+Supr", 5, "Delete"], ["Ctrl+Shift+Esc", 3, "Escape"], ["Win+.", 8, "Period"], ["Alt+Esc", 4, "Escape"]];

// ---------- Plantillas de app (capas) ----------
const TEMPLATES = [
  { name: "OBS Studio", exes: ["obs64.exe"], desc: "Escenas, fuente «Fondo negro» y volumen del micro",
    actions: () => ({ KEY_1: O("next_scene"), KEY_2: O("prev_scene"), KEY_3: O("toggle_source", "Fondo negro"),
      KNOB_CCW: O("volume_down", "Mic/Aux", 2), KNOB_CW: O("volume_up", "Mic/Aux", 2), KNOB_PRESS: O("toggle_mute", "Mic/Aux") }) },
  { name: "Navegador", exes: ["chrome.exe", "msedge.exe", "firefox.exe", "brave.exe"], desc: "Pestañas, reabrir y zoom con la rueda",
    actions: () => ({ KEY_1: K(3, kc("Tab")), KEY_2: K(1, kc("Tab")), KEY_3: K(3, kc("KeyT")),
      KNOB_CCW: Ms(1, 0, -1), KNOB_CW: Ms(1, 0, 1), KNOB_PRESS: K(1, kc("Digit0")) }) },
  { name: "Spotify", exes: ["spotify.exe"], desc: "Pistas, play y volumen",
    actions: () => ({ KEY_1: M(0xB6), KEY_2: M(0xCD), KEY_3: M(0xB5), KNOB_CCW: M(0xEA), KNOB_CW: M(0xE9), KNOB_PRESS: M(0xE2) }) },
  { name: "WoW Forever", exes: ["wow.exe", "wowclassic.exe"], desc: "Mapa, misiones, personaje y cámara; revisa tus teclas en el juego",
    actions: () => ({ KEY_1: K(0, kc("KeyM")), KEY_2: K(0, kc("KeyL")), KEY_3: K(0, kc("KeyC")),
      KNOB_CCW: Ms(0, 0, -1), KNOB_CW: Ms(0, 0, 1), KNOB_PRESS: K(0, kc("KeyP")) }) }
];

// ---------- Render ----------
const hwSig = () => SLOT_ORDER.map(k => slotMessages(k, hwAction(k)).map(hexOf).join("/")).join("|") ;
const layerLabel = () => S.mode === "modes" ? (slotMode() ? slotMode().name : "") : layer().id === "base" ? "Todas las apps" : layer().name;
function collapseAllFolds() {
  document.querySelectorAll("details.fold").forEach(d => { d.open = false; });
}
function refreshUI(opts = {}) {
  const smart = S.mode === "smart", modes = S.mode === "modes";
  document.querySelectorAll(".modes button").forEach(c => { const on = c.dataset.mode === S.mode; c.classList.toggle("active", on); c.setAttribute("aria-checked", on); });
  const hwDirty = deviceConnected && S.flashed !== hwSig();
  const cfgDirty = savedSnap && snapOf() !== savedSnap;
  const dirty = hwDirty || cfgDirty;
  $("btnFlashAll").classList.toggle("alert", dirty);
  $("btnFlashAll").title = dirty ? "Hay cambios sin aplicar · Aplicar al teclado" : "Aplicar cambios al teclado";
  $("btnDiscard").hidden = !cfgDirty;
  if (S.mode === "direct") layerId = "base";
  else if (smart && layerId === "base" && S.layers.length > 1) layerId = S.layers[1].id;
  $("profileWrap").hidden = S.mode !== "direct";
  if (S.mode !== "direct") { $("profilePanel").hidden = true; $("profileToggle").setAttribute("aria-expanded", "false"); }
  $("smartToggle").hidden = !smart;
  $("modeNow").hidden = !modes;
  if (!smart) showSmartPanel(false);
  $("smartCard").hidden = !smart; $("smartRule").hidden = !smart;
  if (!editable()) closeEditorUI();
  $("device").classList.toggle("locked", !editable());   // sin app o sin modo elegido: el dibujo es solo una vista
  $("ledToggle").setAttribute("aria-checked", S.led_mode !== 0);
  $("ledToggleText").textContent = S.led_mode !== 0 ? "Encendida" : "Apagada";
  $("ledNote").textContent = (LED_INFO[S.led_mode] || "Modo sin documentar.") + " El color lo decide el propio teclado: ni el programa del fabricante permite elegirlo.";
  $("ledModes").querySelectorAll("button").forEach(b => b.classList.toggle("active", +b.dataset.led === S.led_mode));
  $("winClose").title = "Cerrar a la bandeja (el docker sigue funcionando)";

  const obsApp = smart && isApp() && (layer().exes || []).some(exe => /(^|[\\/])obs(?:64|32)?\.exe$/i.test(exe));
  $("obsConnection").hidden = !obsApp;
  $("obsTools").hidden = !obsApp;
  if (smart) {
    renderLayers();
    $("layerEdit").hidden = !isApp();
    if (isApp()) { setVal($("layerName"), layer().name); setVal($("layerExes"), layer().exes.join(", ")); }
  }

  renderModes();
  renderCtx();
  SLOT_ORDER.forEach(k => {
    const a = shown(k), box = document.querySelector(`[data-target="${k}"]`);
    box.classList.toggle("inherit", isApp() && !own(k));
    const text = a ? textOf(a) : "—";
    $("lbl_" + k).textContent = (k === "KNOB_CCW" ? "↺ " : k === "KNOB_CW" ? "↻ " : "") + text;
  });

  const a = cur(), isKnob = currentTarget.startsWith("KNOB"), inherited = isApp() && !own(currentTarget);
  $("selectedLabel").textContent = $("editor").hidden ? "" : TARGET_NAME[currentTarget] + (S.mode !== "direct" ? ` · ${layerLabel()}` : "");
  $("comboCount").textContent = (a.type === "media" || a.type === "obs") ? "" : `${countOf(a)} / ${MAX_KEYS} teclas`;
  $("curMeta").textContent = TYPE_NAME[a.type];
  $("curCard").classList.toggle("inherited", inherited);
  $("curLabel").textContent = inherited ? "Sin definir · usa Directo" : "Asignado";
  $("btnClear").title = isApp() ? "Quitar (usar Directo)" : "Borrar";
  $("btnClear").disabled = isApp() ? !own(currentTarget) : false;
  $("btnTest").hidden = !API.ok;
  renderChips($("curChips"), a);
  $("speedRow").hidden = !speedApplies(a);
  const speedOptions = isWheelVolume(currentTarget, a) ? [[1, "±1 %"], [2, "±2 %"], [3, "±3 %"], [5, "±5 %"]] : SPEEDS;
  renderSeg($("speedSeg"), a.speed, v => {
    const volume = x => x && x.type === "media" && (x.code === 0xE9 || x.code === 0xEA);
    if (isKnob && volume(a) && volume(shown("KNOB_CCW")) && volume(shown("KNOB_CW"))) {
      ["KNOB_CCW", "KNOB_CW"].forEach(k => { layer().actions[k] = { ...shown(k), speed: v }; });
      knobSpeed = v; persist(); refreshUI();
    } else setAction({ ...a, speed: v });
  }, speedOptions);

  $("knobTargetSeg").hidden = !isKnob;
  if (isKnob) {
    renderSeg($("knobTargetSeg"), currentTarget, v => {
      currentTarget = v;
      document.querySelectorAll("[data-target]").forEach(n => n.classList.toggle("selected", n.dataset.target === v));
      refreshUI({ quiet: true });
    }, [["KNOB_CCW", "↺ Izq."], ["KNOB_PRESS", "● Pulsar"], ["KNOB_CW", "↻ Der."]]);
  }
  $("knobTools").hidden = !isKnob;
  if (isKnob) {
    const box = $("recipes"); box.innerHTML = "";
    const mapOf = r => `↺ ${textOf(r.ccw)} · ↻ ${textOf(r.cw)}${r.press ? " · ● " + textOf(r.press) : ""}`;
    RECIPES.forEach(r => {
      const on = sameAction(shown("KNOB_CCW"), r.ccw) && sameAction(shown("KNOB_CW"), r.cw);
      const b = el("button", "tile" + (on ? " active" : ""));
      b.innerHTML = ic(r.icon) + `<span>${r.name}</span>`;
      b.title = r.desc + "\n" + mapOf(r);
      b.addEventListener("mouseenter", () => { $("recipeMap").textContent = mapOf(r); });
      b.addEventListener("click", () => {
        const acts = layer().actions;
        acts.KNOB_CCW = withSpeed(r.ccw, knobSpeed); acts.KNOB_CW = withSpeed(r.cw, knobSpeed);
        if (r.press) acts.KNOB_PRESS = withSpeed(r.press, knobSpeed);
        persist(); refreshUI(); toast(`Rueda: ${r.name}`);
      });
      box.appendChild(b);
    });
    const act = RECIPES.find(r => sameAction(shown("KNOB_CCW"), r.ccw) && sameAction(shown("KNOB_CW"), r.cw));
    $("recipeMap").textContent = act ? mapOf(act) : "";
    const left = shown("KNOB_CCW") || EMPTY, right = shown("KNOB_CW") || EMPTY;
    if (speedApplies(a)) knobSpeed = a.speed;
    $("knobSpeedRow").hidden = false;
    $("knobSpeedRow").classList.toggle("dim", !(speedApplies(left) || speedApplies(right)));
    renderSeg($("knobSpeedSeg"), knobSpeed, v => {
      knobSpeed = v;
      ["KNOB_CCW", "KNOB_CW"].forEach(k => { const x = shown(k); if (x) layer().actions[k] = withSpeed(x, v); });
      persist(); refreshUI();
    }, isWheelVolume("KNOB_CCW", left) && isWheelVolume("KNOB_CW", right) ? [[1, "±1 %"], [2, "±2 %"], [3, "±3 %"], [5, "±5 %"]] : SPEEDS);
  }

  document.querySelectorAll("#obsOps .opt").forEach(o => o.classList.toggle("active", a.type === "obs" && a.op === o.dataset.op));
  const od = a.type === "obs" ? OBS_BY_OP[a.op] : null;
  $("obsTargetRow").hidden = !(od && od.needs);
  if (od && od.needs) { $("obsTargetLabel").textContent = od.needs; setVal($("obsTarget"), a.target || ""); }
  setVal($("obsHost"), S.obs.host); setVal($("obsPort"), S.obs.port); setVal($("obsPass"), S.obs.password);

  if (!opts.quiet) slotMessages(currentTarget, hwAction(currentTarget)).slice(1, -1).forEach(m => logHex(`PREVIEW [${currentTarget}]`, m));
}
function logHex(tag, bytes) { logLine(`[${new Date().toLocaleTimeString()}] ${tag}: 03 ${hexOf(bytes)} ...`); }

// Icono Lucide según el programa de la capa (el nombre sigue en el título y para lectores de pantalla).
const APP_ICONS = [[/whatsapp|telegram|discord|slack|teams/, "message-circle"], [/obs/, "clapperboard"], [/spotify/, "music"],
  [/chrome|msedge|edge|firefox|brave|opera/, "globe"], [/claude|chatgpt|openai/, "bot"], [/notepad/, "notebook-pen"],
  [/wow/, "gamepad-2"], [/word|excel|powerpoint|onenote|code|notion/, "file-text"]];
function appIcon(l) {
  const text = [l.name, ...(l.exes || [])].join(" ").toLowerCase();
  const hit = APP_ICONS.find(([re]) => re.test(text));
  return hit ? hit[1] : "app-window";
}
// Nombre corto para la pestaña: la primera palabra del programa («whatsapp-web.chrome» → «whatsapp»).
const shortName = name => name.replace(/\.exe$/i, "").split(/[-._\s]/)[0].slice(0, 10);
function renderLayers() {
  const bar = $("layerWrap"); bar.innerHTML = "";
  S.layers.slice(1).forEach(l => {
    const b = el("button", "layer-tab icon-only" + (l.id === layerId ? " active" : ""));
    b.innerHTML = `<span class="tab-name"></span>` + ic(appIcon(l)) + `<span class="live"></span>`;
    b.querySelector(".tab-name").textContent = shortName(l.name); b.dataset.layer = l.id;
    b.setAttribute("aria-label", l.name);
    b.title = `${l.name} · ${TRIGGERS[S.trigger]} + botón${l.exes.length ? " · " + l.exes.join(", ") : " · sin programa"}`;
    b.addEventListener("click", () => { if (l.id !== layerId) { layerId = l.id; closeEditorUI(); collapseAllFolds(); swapFx(); refreshUI(); } });
    bar.appendChild(b);
  });
  const add = el("button", "layer-tab add"); add.innerHTML = ic("plus") + "<span>Añadir app</span>"; add.title = "Atajos propios para otra app";
  add.addEventListener("click", openAdd);
  bar.appendChild(add);
}
// Cómo se activa lo que estás editando: lo mismo en las tres pestañas, sobre el dibujo del docker.
function renderCtx() {
  const kbd = s => `<kbd>${s}</kbd>`, plus = ic("plus"), box = $("deviceCtx");
  let keys = kbd("Botón"), why = "pulsado solo, en cualquier app", name = "";
  if (S.mode === "smart") {
    keys = `${kbd(TRIGGERS[S.trigger])}${plus}${kbd("Botón")}`;
    if (layerId === "base") why = "añade una app para darle atajos propios";
    else { why = "con <b></b> en primer plano"; name = layer().name; }
  } else if (S.mode === "modes") {
    if (slotMode()) { why = "con el modo <b></b> activo"; name = slotMode().name; }
    else why = "elige una plantilla para este modo";
  }
  box.innerHTML = `${keys}<span class="why">${why}</span>`;
  const b = box.querySelector("b"); if (b) b.textContent = name;
}
// Modos: el carril a la izquierda del docker selecciona el hueco y abre su menú (nombre, plantilla, vaciar).
// El panel «Modos de trabajo» (icono de ajustes) solo elige la plantilla que recibe el hueco elegido.
let modeMenuOpen = false;
// Iconos que se pueden dar a un modo: todos tienen equivalente en el aviso nativo de Windows.
const MODE_ICONS = [["music", "Música"], ["volume-2", "Volumen"], ["mic", "Micrófono"], ["gamepad-2", "Juegos"], ["clapperboard", "Vídeo"], ["film", "Cine"],
  ["brush", "Edición"], ["notebook-pen", "Notas"], ["code-xml", "Código"], ["terminal", "Terminal"], ["app-window", "Ventanas"], ["globe", "Web"],
  ["message-circle", "Chat"], ["zap", "Rápido"], ["sparkles", "Destacado"], ["sliders-horizontal", "Ajustes"]];
function iconPicker(current, onPick) {
  const box = el("div", "icon-picker"); box.setAttribute("role", "radiogroup"); box.setAttribute("aria-label", "Icono del modo");
  MODE_ICONS.forEach(([name, label]) => {
    const b = el("button", "icon-opt" + (name === current ? " active" : "")); b.type = "button";
    b.setAttribute("role", "radio"); b.setAttribute("aria-checked", String(name === current)); b.title = label; b.setAttribute("aria-label", label);
    b.innerHTML = ic(name);
    b.addEventListener("click", () => {
      onPick(name);
      box.querySelectorAll(".icon-opt").forEach(o => { o.classList.toggle("active", o === b); o.setAttribute("aria-checked", String(o === b)); });
    });
    box.appendChild(b);
  });
  return box;
}
// Referencia visual: el docker en pequeño, solo en la vista previa de una plantilla (donde decides qué hará cada botón).
function miniDocker(pick) {
  const text = k => { const a = pick(k); return a ? textOf(a) : "—"; };
  const box = el("div", "mini-docker"), keys = el("div", "mini-keys"), knob = el("span", "mini-knob");
  ["KEY_1", "KEY_2", "KEY_3"].forEach((k, i) => {
    const key = el("span", "mini-key"); key.append(el("small", "", String(i + 1)), el("b", "", text(k))); key.title = `${TARGET_NAME[k]}: ${text(k)}`; keys.appendChild(key);
  });
  knob.append(el("b", "", text("KNOB_PRESS")), el("small", "", `↺ ${text("KNOB_CCW")} · ↻ ${text("KNOB_CW")}`));
  knob.title = `Rueda · giro izquierda: ${text("KNOB_CCW")} · pulsar: ${text("KNOB_PRESS")} · giro derecha: ${text("KNOB_CW")}`;
  box.append(keys, knob);
  box.setAttribute("role", "img");
  box.setAttribute("aria-label", "Referencia del docker: " + SLOT_ORDER.map(k => `${TARGET_NAME[k]} ${text(k)}`).join(", "));
  return box;
}
function fillMini(host, pick, caption) { host.replaceChildren(miniDocker(pick), el("small", "mini-cap", caption)); }
function renderModes() {
  renderRail();
  const m = slotMode();
  const btn = $("modeNow"), on = liveMode === modeIdx, label = on ? "Volver a Directo" : "Activar este modo ahora";
  btn.disabled = !API.ok || !m;
  btn.innerHTML = ic(on ? "undo-2" : "play"); btn.title = label; btn.setAttribute("aria-label", label);
  btn.classList.toggle("on", on);
}
function renderRail() {
  const rail = $("modeRail"), mode = S.mode;
  rail.querySelectorAll(".mode-rail-btn").forEach(n => n.remove());
  rail.removeAttribute("aria-hidden");
  if (mode === "direct") { rail.removeAttribute("role"); rail.removeAttribute("aria-label"); rail.setAttribute("aria-hidden", "true"); }
  else { rail.setAttribute("role", "radiogroup"); rail.setAttribute("aria-label", mode === "smart" ? "Tecla de activación" : "Modos de trabajo"); }
  if (mode === "direct") {   // Directo reserva el mismo sitio: sus iconos llegarán más adelante
    for (let i = 0; i < 3; i++) {
      const b = el("button", "mode-rail-btn placeholder"); b.type = "button"; b.disabled = true; b.tabIndex = -1; b.title = "Próximamente";
      b.innerHTML = ic("minus"); rail.appendChild(b);
    }
    return renderMenu();
  }
  if (mode === "smart") {   // Inteligente: la tecla de activación, una sola, vive en el carril
    Object.entries(TRIGGERS).forEach(([key, label]) => {
      const on = S.trigger === key, b = el("button", "mode-rail-btn" + (on ? " active" : ""));
      b.type = "button"; b.setAttribute("role", "radio"); b.setAttribute("aria-checked", String(on));
      const tip = `${label}: mantén ${label} y pulsa un botón`; b.title = tip; b.setAttribute("aria-label", tip);
      b.append(el("span", "rail-key", label));
      b.addEventListener("click", () => { if (S.trigger === key) return; S.trigger = key; persist(); refreshUI(); });
      rail.appendChild(b);
    });
    return renderMenu();
  }
  S.modes.forEach((m, i) => {
    const b = el("button", "mode-rail-btn" + (i === modeIdx ? " active" : "") + (i === liveMode ? " is-live" : "") + (m ? "" : " empty"));
    b.type = "button"; b.setAttribute("role", "radio"); b.setAttribute("aria-checked", String(i === modeIdx));
    b.innerHTML = `<kbd>${i + 1}</kbd>` + ic(m ? m.icon : "plus") + `<i class="live"></i>`;
    const label = m ? `${m.name} · Ctrl+Shift+${i + 1}` : `Hueco libre ${i + 1}: elegir plantilla`;
    b.title = label; b.setAttribute("aria-label", label);
    b.addEventListener("click", () => railClick(i));
    rail.appendChild(b);
  });
  renderMenu();
}
function railClick(i) {
  if (i === modeIdx) modeMenuOpen = !modeMenuOpen;
  else { modeIdx = i; modeMenuOpen = true; }
  menuView = S.modes[i] ? "main" : "tpl"; menuIconsOpen = false; selectedPreset = null;   // hueco libre: directo a las plantillas
  closeEditorUI(); swapFx(); refreshUI();
}
let menuIconsOpen = false, menuView = "main";   // main: nombre, icono y acciones · tpl: plantillas
function closeModeMenu() { if (!modeMenuOpen) return; modeMenuOpen = false; menuIconsOpen = false; menuView = "main"; selectedPreset = null; renderMenu(); }
function menuHead(title, lead) {
  const head = el("div", "mode-menu-head"), close = el("button", "close-editor", "×");
  close.type = "button"; close.setAttribute("aria-label", "Cerrar menú del modo"); close.addEventListener("click", closeModeMenu);
  head.append(lead, el("span", "mode-menu-title", title), close);
  return head;
}
function renderMenu() {
  const menu = $("modeMenu"), m = S.modes[modeIdx];
  menu.hidden = !(modeMenuOpen && S.mode === "modes");
  menu.innerHTML = "";
  if (menu.hidden) { menuIconsOpen = false; menuView = "main"; return; }
  menu.classList.toggle("tpl", menuView === "tpl" || !m);
  if (menuView === "tpl" || !m) return renderTplView(menu, m);
  const lead = el("button", "mode-icon-btn"); lead.innerHTML = ic(m.icon);
  lead.type = "button"; lead.title = "Cambiar el icono"; lead.setAttribute("aria-label", "Cambiar el icono"); lead.setAttribute("aria-expanded", String(menuIconsOpen));
  lead.addEventListener("click", () => { menuIconsOpen = !menuIconsOpen; renderMenu(); });
  const head = menuHead(`Hueco ${modeIdx + 1} · Ctrl+Shift+${modeIdx + 1}`, lead);
  const input = el("input", "mode-inline-name"); input.type = "text"; input.maxLength = 30; input.value = m.name;
  input.setAttribute("aria-label", "Nombre del modo");
  input.addEventListener("keydown", e => { if (e.key === "Enter") input.blur(); else if (e.key === "Escape") { input.value = m.name; input.blur(); } });
  input.addEventListener("change", () => { m.name = input.value.trim().slice(0, 30) || `Modo ${modeIdx + 1}`; persist(); renderModes(); renderCtx(); });
  const actions = el("div", "mode-menu-actions");
  const tpl = el("button"); tpl.type = "button"; tpl.innerHTML = ic("layout-grid") + "<span>Plantilla</span>";
  tpl.title = "Elegir otra plantilla para este hueco";
  tpl.addEventListener("click", () => { menuView = "tpl"; menuIconsOpen = false; selectedPreset = null; renderMenu(); });
  const clear = el("button", "danger"); clear.type = "button"; clear.innerHTML = ic("trash-2") + "<span>Vaciar</span>";
  clear.title = "Quita el modo de este hueco. La plantilla no se borra.";
  clear.addEventListener("click", () => {
    if (!window.confirm(`¿Vaciar el hueco ${modeIdx + 1}? La plantilla «${m.name}» sigue disponible.`)) return;
    S.modes[modeIdx] = null; modeMenuOpen = false; menuIconsOpen = false; menuView = "main"; persist(); closeEditorUI(); swapFx(); refreshUI();
  });
  actions.append(tpl, clear);
  const parts = [head, input];
  if (menuIconsOpen) parts.push(iconPicker(m.icon, name => { m.icon = name; persist(); renderModes(); }));
  menu.append(...parts, actions);
}
// Plantillas: la misma cuadrícula de chips (icono + nombre) que «Atajos para»; la descripción va en la vista previa.
function renderTplView(menu, m) {
  const lead = el("span", "mode-icon"); lead.innerHTML = ic("layout-grid");
  const head = menuHead(`Hueco ${modeIdx + 1} · ${m ? "cambiar plantilla" : "elige una plantilla"}`, lead);
  if (m) {
    const back = el("button", "mode-icon-btn"); back.type = "button"; back.innerHTML = ic("arrow-left");
    back.title = "Volver al menú del hueco"; back.setAttribute("aria-label", back.title);
    back.addEventListener("click", () => { menuView = "main"; selectedPreset = null; renderMenu(); });
    head.replaceChild(back, head.firstChild);
  }
  const grid = el("div", "chip-grid");
  PRESETS.forEach(p => grid.appendChild(chip(p.name, p.icon, p.desc, () => {
    selectedPreset = p;
    if (p.blank) { blankIcon = "sliders-horizontal"; blankName = `Modo ${modeIdx + 1}`; }
    renderMenu();
  }, p === selectedPreset)));
  menu.append(head, grid);
  if (selectedPreset) menu.appendChild(presetPreview(selectedPreset));
}
function presetPreview(p) {
  const acts = p.actions(), box = el("div", "preset-preview"), top = el("div", "preset-top");
  const mini = el("div", "mini-ref");
  fillMini(mini, k => acts[k] || (p.blank ? S.layers[0].actions[k] : undefined), p.blank ? "Hereda de Directo hasta que lo cambies" : "Así queda el docker");
  const info = el("div", "preset-info");
  info.append(el("strong", "", p.name), el("p", "muted", p.note && !p.blank ? `${p.desc} ${p.note}` : p.desc));
  const go = el("button", "primary", p.blank ? "Crear modo" : "Usar en este modo"); go.type = "button";
  go.addEventListener("click", () => applyPreset(p));
  top.append(mini, info);
  if (p.blank) {
    const name = el("input", "mode-inline-name"); name.type = "text"; name.maxLength = 30; name.value = blankName; name.setAttribute("aria-label", "Nombre del modo");
    name.addEventListener("input", () => { blankName = name.value; });
    const row = el("div", "blank-row"); row.append(name, go);
    box.append(el("p", "muted", p.desc), row, iconPicker(blankIcon, n => { blankIcon = n; }));
  } else { info.appendChild(go); box.appendChild(top); }
  return box;
}
function applyPreset(p) {
  const m = slotMode();
  if (m && Object.keys(m.actions).length && !window.confirm(`«${p.name}» reemplazará los atajos del modo «${m.name}». ¿Continuar?`)) return;
  const name = p.blank ? (blankName.trim().slice(0, 30) || `Modo ${modeIdx + 1}`) : p.name;
  modeMenuOpen = false; menuIconsOpen = false; menuView = "main"; selectedPreset = null;
  fillMode({ name, icon: p.blank ? blankIcon : p.icon, actions: p.actions() });
  toast(p.blank ? `Modo ${modeIdx + 1}: ${name}. Lo que no definas hace lo de Directo` : `Modo ${modeIdx + 1}: ${name}`);
}
document.addEventListener("click", e => { if (modeMenuOpen && e.target.isConnected && !$("modeRail").contains(e.target) && !$("modeMenu").contains(e.target)) closeModeMenu(); });
// Con el docker bloqueado (sin plantilla o sin app), la pieza lleva a donde se resuelve.
function lockedHint() {
  if (S.mode === "smart") return openAdd();
  if (S.mode === "modes") { modeMenuOpen = true; menuView = "tpl"; selectedPreset = null; return refreshUI(); }
  toast("Elige una plantilla o crea un modo en blanco", true);
}
function fillMode(m) { S.modes[modeIdx] = m; persist(); closeEditorUI(); refreshUI(); }
function setAction(a) { layer().actions[currentTarget] = a; persist(); refreshUI(); }

// ---------- Controles estáticos ----------
(function build() {
  OBS_OPS.forEach(o => {
    const b = el("button", "opt", o.label);
    b.dataset.op = o.op;
    b.addEventListener("click", () => {
      const a = cur();
      setAction(O(o.op, a.type === "obs" && OBS_BY_OP[a.op].needs === o.needs ? a.target : (o.def || ""), o.speed ? speedOf(a) : 1));
    });
    $("obsOps").appendChild(b);
  });
  LIB.forEach(([name, mod, dom]) => {
    const b = el("button", "", name);
    b.addEventListener("click", () => { setAction(K(mod, kc(dom))); toast("Asignado: " + name); });
    $("lib").appendChild(b);
  });
})();

// ---------- Perfiles de Directo ----------
function renderProfiles() {
  const list = $("profileList"); list.innerHTML = "";
  S.profiles.forEach((profile, index) => {
    const row = el("div", "profile-row"), select = el("button", "profile-select", profile.name), remove = el("button", "profile-delete");
    select.title = `Seleccionar ${profile.name}`;
    select.addEventListener("click", () => {
      if (savedSnap && JSON.stringify(S.layers[0].actions) !== JSON.stringify(JSON.parse(savedSnap).layers[0].actions) && !window.confirm("Hay cambios sin confirmar. ¿Cambiar de perfil?")) return;
      S.layers[0].actions = JSON.parse(JSON.stringify(profile.actions)); persist(); closeEditorUI(); refreshUI();
      $("profilePanel").hidden = true; $("profileToggle").setAttribute("aria-expanded", "false"); toast(`Perfil: ${profile.name}`);
    });
    remove.type = "button"; remove.innerHTML = ic("trash-2"); remove.title = `Eliminar ${profile.name}`; remove.setAttribute("aria-label", remove.title);
    remove.addEventListener("click", () => { if (!window.confirm(`¿Eliminar el perfil «${profile.name}»?`)) return; S.profiles.splice(index, 1); persist(); renderProfiles(); });
    row.append(select, remove); list.appendChild(row);
  });
}
$("profileToggle").addEventListener("click", () => { const panel = $("profilePanel"); panel.hidden = !panel.hidden; $("profileToggle").setAttribute("aria-expanded", String(!panel.hidden)); if (!panel.hidden) renderProfiles(); });
$("profileSave").addEventListener("click", () => {
  const name = $("profileName").value.trim().slice(0, 12);
  if (!name) return toast("Escribe un nombre para el perfil", true);
  if (S.profiles.some(p => p.name.toLocaleLowerCase() === name.toLocaleLowerCase())) return toast("Ya existe un perfil con ese nombre", true);
  const confirmed = savedSnap && JSON.parse(savedSnap).layers[0].actions;
  if (!confirmed || JSON.stringify(confirmed) !== JSON.stringify(S.layers[0].actions)) return toast("Confirma primero los cambios con el botón ✓", true);
  S.profiles.push({name, actions: JSON.parse(JSON.stringify(confirmed))}); $("profileName").value = ""; persist(); renderProfiles(); toast("Perfil guardado");
});
document.addEventListener("click", e => { if (!$("profileWrap").contains(e.target) && !$("profilePanel").contains(e.target)) { $("profilePanel").hidden = true; $("profileToggle").setAttribute("aria-expanded", "false"); } });

function showSmartPanel(show) {
  if (show) closeEditorUI();
  $("smartPanel").hidden = !show;
  $("smartToggle").setAttribute("aria-expanded", String(show));
}
$("smartToggle").addEventListener("click", () => showSmartPanel($("smartPanel").hidden));
$("smartClose").addEventListener("click", () => { showSmartPanel(false); $("smartToggle").focus(); });

// ---------- Eventos de la interfaz ----------
// Clic directo en una pieza del docker = abre grabación directa.
document.querySelectorAll("[data-target]").forEach(t => {
  t.addEventListener("click", () => {
    if (!editable()) return lockedHint();
    currentTarget = t.dataset.target;
    knobSpeed = cur().speed || 1;
    if (!$("editor").hidden) {
      document.querySelectorAll("[data-target]").forEach(n => n.classList.toggle("selected", n === t));
      const penKey = currentTarget.startsWith("KNOB") ? "KNOB" : currentTarget;
      document.querySelectorAll(".edit-pen").forEach(p => p.classList.toggle("active", p.dataset.edit === penKey));
    }
    refreshUI({ quiet: true });
    recStart();
  });
});
// Clic en el lápiz debajo de cada pieza = abre o cierra el menú 2 para edición en detalle.
document.querySelectorAll(".edit-pen").forEach(btn => {
  btn.addEventListener("click", () => {
    if (!editable()) return lockedHint();
    const key = btn.dataset.edit;
    if (!$("editor").hidden && btn.classList.contains("active")) return closeEditorUI();
    currentTarget = key === "KNOB" ? (currentTarget.startsWith("KNOB") ? currentTarget : "KNOB_PRESS") : key;
    document.querySelectorAll(".edit-pen").forEach(p => p.classList.toggle("active", p === btn));
    document.querySelectorAll("[data-target]").forEach(n => n.classList.toggle("selected", n.dataset.target === currentTarget));
    collapseAllFolds();
    $("editor").hidden = false;
    knobSpeed = cur().speed || 1;
    refreshUI();
  });
});
function closeEditorUI() {
  $("editor").hidden = true;
  document.querySelectorAll("[data-target]").forEach(n => n.classList.remove("selected"));
  document.querySelectorAll(".edit-pen").forEach(p => p.classList.remove("active"));
  $("selectedLabel").textContent = "";
}
$("closeEditor").addEventListener("click", closeEditorUI);
document.addEventListener("keydown", e => { if (e.key === "Escape" && !$("sysMenu").hidden) { setSys(false); $("btnSys").focus(); } else if (e.key === "Escape" && !$("editor").hidden) { closeEditorUI(); } else if (e.key === "Escape" && !$("smartPanel").hidden && !$("addOverlay").classList.contains("show")) { showSmartPanel(false); $("smartToggle").focus(); } else if (e.key === "Escape") closeModeMenu(); });
function showLighting(show) {
  $("lightingPanel").hidden = !show;
  $("btnLighting").setAttribute("aria-expanded", String(show));
}
$("btnLighting").addEventListener("click", () => showLighting($("lightingPanel").hidden));
$("closeLighting").addEventListener("click", () => { showLighting(false); $("btnLighting").focus(); });
$("device").addEventListener("keydown", e => {
  const t = e.target.closest("[data-target]");
  if (!t) return;
  if (e.key === "Enter" || e.key === " ") { e.preventDefault(); t.click(); }
  else if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
    e.preventDefault();
    const i = SLOT_ORDER.indexOf(t.dataset.target), n = SLOT_ORDER[(i + (e.key === "ArrowRight" ? 1 : SLOT_ORDER.length - 1)) % SLOT_ORDER.length];
    const next = document.querySelector(`[data-target="${n}"]`); next.focus(); next.click();
  }
});
document.querySelectorAll(".modes button").forEach(c => c.addEventListener("click", () => {
  if (S.mode === c.dataset.mode) return;
  S.mode = c.dataset.mode; modeMenuOpen = false; persist(); closeEditorUI(); collapseAllFolds(); showLighting(false); swapFx(); refreshUI();
}));
// ---------- Luz ----------
// Solo existen los modos 0, 1 y 2 (los mismos que ofrece el programa del fabricante); descripciones comprobadas en el teclado real.
const LED_INFO = {
  0: "Luz apagada.",
  1: "Cada pulsación enciende la tecla con el siguiente color de la serie (azul, rojo, verde…).",
  2: "Una pulsación lanza un ciclo de colores que recorre las teclas 1, 2 y 3."
};
let ledOn = S.led_mode || 1;                      // último modo encendido, para el interruptor
async function setLed(mode) {
  mode = Math.max(0, Math.min(255, mode | 0));
  S.led_mode = mode; if (mode) ledOn = mode;
  persist(); refreshUI({ quiet: true });
  if (!API.ok) return toast("La luz solo se aplica con la app RevienDocker abierta", true);
  try {
    const r = await api("/api/led", { mode });
    if (r.ok === false) toast("No se pudo cambiar la luz: " + r.error, true);
    else toast(r.sent ? "Luz aplicada" : "Simulador: no hay teclado conectado", !r.sent);
  } catch (_) { toast("No se pudo cambiar la luz", true); }
}
[[0, "Apagada"], [1, "Al pulsar"], [2, "Ciclo"]].forEach(([v, label]) => {
  const b = el("button", "", label); b.dataset.led = v; b.setAttribute("role", "radio");
  b.addEventListener("click", () => setLed(v)); $("ledModes").appendChild(b);
});
$("ledToggle").addEventListener("click", () => setLed(S.led_mode ? 0 : ledOn));
$("btnClear").addEventListener("click", () => {
  if (isApp()) { delete layer().actions[currentTarget]; persist(); refreshUI(); }
  else setAction(K(0, 0));
});
$("btnInvert").addEventListener("click", () => {
  const acts = layer().actions, a = shown("KNOB_CCW"), b = shown("KNOB_CW");
  acts.KNOB_CCW = b; acts.KNOB_CW = a;
  persist(); refreshUI(); toast("Sentido de giro invertido");
});
$("btnTest").addEventListener("click", () => {
  const a = cur();
  if (!hasMain(a) && !a.mod) return toast("Esta acción está vacía", true);
  api("/api/run", { action: a, delay: 3 }).then(() => toast("Se ejecuta en 3 s: cambia a la ventana donde quieras probarlo")).catch(() => toast("No se pudo ejecutar", true));
});

$("obsTarget").addEventListener("input", e => { const a = cur(); if (a.type === "obs") { layer().actions[currentTarget] = { ...a, target: e.target.value }; persist(); refreshUI({ quiet: true }); } });
["obsHost", "obsPort", "obsPass"].forEach(id => $(id).addEventListener("input", () => {
  S.obs = { host: $("obsHost").value.trim() || "127.0.0.1", port: parseInt($("obsPort").value, 10) || 4455, password: $("obsPass").value };
  persist();
}));
$("layerName").addEventListener("input", e => { layer().name = e.target.value.trim() || layer().name; persist(); renderLayers(); $("selectedLabel").textContent = TARGET_NAME[currentTarget] + " · " + layerLabel(); });
$("layerExes").addEventListener("input", e => { layer().exes = e.target.value.split(",").map(x => x.trim().toLowerCase()).filter(Boolean); persist(); });
let delArm = null;
const delLabel = () => { $("btnDelLayer").querySelector("span").textContent = delArm ? "¿Seguro? Clic otra vez" : "Quitar app"; };
$("btnDelLayer").addEventListener("click", () => {
  if (!delArm) { delArm = setTimeout(() => { delArm = null; delLabel(); }, 3000); delLabel(); return; }
  clearTimeout(delArm); delArm = null; delLabel();
  S.layers = S.layers.filter(l => l.id !== layerId); layerId = "base"; persist(); swapFx(); refreshUI();
});
// ---------- Plantillas con vista previa ----------
const F = n => K(0, kc("F" + n));
const PRESETS = [
  { id: "media", name: "Música y volumen", icon: "music", desc: "Controla la reproducción y el sonido.",
    actions: () => ({ KEY_1: M(0xB6), KEY_2: M(0xCD), KEY_3: M(0xB5), KNOB_CCW: M(0xEA), KNOB_PRESS: M(0xE2), KNOB_CW: M(0xE9) }) },
  { id: "wow", name: "WoW Forever", icon: "gamepad-2", desc: "Mapa, misiones y personaje; rueda para la cámara.",
    note: "Usa M, L, C y P. Comprueba las teclas asignadas en el juego; la cámara usa la rueda del ratón.",
    actions: () => ({ KEY_1: K(0, kc("KeyM")), KEY_2: K(0, kc("KeyL")), KEY_3: K(0, kc("KeyC")), KNOB_CCW: Ms(0, 0, -1), KNOB_PRESS: K(0, kc("KeyP")), KNOB_CW: Ms(0, 0, 1) }) },
  { id: "browser", name: "Navegación", icon: "app-window", desc: "Pestañas y zoom del navegador.",
    actions: () => ({ KEY_1: K(3, kc("Tab")), KEY_2: K(3, kc("KeyT")), KEY_3: K(1, kc("Tab")), KNOB_CCW: Ms(1, 0, -1), KNOB_PRESS: K(1, kc("Digit0")), KNOB_CW: Ms(1, 0, 1) }) },
  { id: "meeting", name: "Reuniones", icon: "mic", desc: "Atajos de ejemplo para videollamadas.",
    note: "Los atajos de micrófono y cámara dependen de la aplicación. Ajusta las teclas según tu programa.",
    actions: () => ({ KEY_1: K(3, kc("KeyM")), KEY_2: K(3, kc("KeyO")), KEY_3: K(4, kc("Tab")), KNOB_CCW: M(0xEA), KNOB_PRESS: M(0xE2), KNOB_CW: M(0xE9) }) },
  { id: "edit", name: "Edición", icon: "brush", desc: "Deshacer, rehacer y zoom.",
    actions: () => ({ KEY_1: K(1, kc("KeyZ")), KEY_2: K(1, kc("KeyS")), KEY_3: K(1, kc("KeyY")), KNOB_CCW: Ms(1, 0, -1), KNOB_PRESS: K(1, kc("Digit0")), KNOB_CW: Ms(1, 0, 1) }) },
  { id: "dev", name: "Trabajo diario", icon: "code-xml", desc: "Copiar, pegar y desplazarte.",
    actions: () => ({ KEY_1: K(1, kc("KeyC")), KEY_2: K(1, kc("KeyV")), KEY_3: K(0, kc("Enter")), KNOB_CCW: Ms(0, 0, 1), KNOB_PRESS: K(0, kc("Space")), KNOB_CW: Ms(0, 0, -1) }) },
  { id: "obs", name: "OBS por atajos", icon: "clapperboard", desc: "Atajos configurables para escenas y micrófono.",
    note: "Primero asigna Ctrl+Shift+F13/F14/F15 y Ctrl+M en los ajustes de atajos de OBS.",
    actions: () => ({ KEY_1: K(3, kc("F13")), KEY_2: K(3, kc("F14")), KEY_3: K(3, kc("F15")), KNOB_CCW: M(0xEA), KNOB_PRESS: K(1, kc("KeyM")), KNOB_CW: M(0xE9) }) },
  { id: "fkeys", name: "Teclas fantasma", icon: "ghost", desc: "F13–F18 para asignarlas en otras aplicaciones.",
    note: "Son teclas poco habituales: no hacen nada por sí solas. Asígnalas a acciones en otra app. RevienDocker las envía al pulsar el botón.",
    actions: () => ({ KEY_1: F(13), KEY_2: F(14), KEY_3: F(15), KNOB_CCW: F(16), KNOB_PRESS: F(18), KNOB_CW: F(17) }) }
];
PRESETS.push({ id: "blank", name: "Nuevo modo", icon: "plus", desc: "Empieza de cero: lo que no definas hace lo de Directo.",
  note: "Elige nombre e icono. Después asigna cada botón con su lápiz.", blank: true, actions: () => ({}) });
let selectedPreset = null, blankIcon = "sliders-horizontal", blankName = "";
$("modeNow").addEventListener("click", () => api("/api/mode", { slot: modeIdx }).then(updateEngineUI).catch(() => toast("No se pudo cambiar de modo", true)));

// ---------- Capas: añadir app ----------
function slug(s) { return s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 30) || "app"; }
function addLayer(name, exes, actions) {
  const found = S.layers.find(l => l !== S.layers[0] && exes.some(x => l.exes.includes(x)));
  if (found) { layerId = found.id; toast("Esa app ya tiene capa"); }
  else {
    let id = slug(name), n = 2;
    while (S.layers.some(l => l.id === id)) id = slug(name) + "-" + n++;
    S.layers.push({ id, name, exes, actions: actions || {} }); layerId = id;
  }
  closeAdd(); persist(); swapFx(); refreshUI();
}
// Chip de icono + nombre: el mismo formato en «Atajos para», «Añadir una app» y las plantillas de Modos.
function chip(name, icon, title, onClick, active) {
  const b = el("button", "layer-tab icon-only" + (active ? " active" : "")); b.type = "button";
  b.innerHTML = `<span class="tab-name"></span>` + ic(icon);
  b.querySelector(".tab-name").textContent = name; b.title = title; b.setAttribute("aria-label", title);
  b.addEventListener("click", onClick);
  return b;
}
function openAdd() {
  const tpl = $("tplList"); tpl.innerHTML = "";
  TEMPLATES.forEach(t => tpl.appendChild(chip(t.name, appIcon({ name: t.name, exes: t.exes }), t.desc, () => addLayer(t.name, t.exes, t.actions()))));
  const win = $("winList"); win.innerHTML = ""; $("winHint").textContent = "";
  if (API.ok) {
    api("/api/windows").then(r => {
      const seen = new Set(S.layers.flatMap(l => l.exes || []));
      const open = r.windows.filter(w => { const k = w.exe.toLowerCase(); if (seen.has(k) || SELF_EXE.test(k)) return false; seen.add(k); return true; });
      if (!open.length) $("winHint").textContent = "No hay más apps abiertas que añadir.";
      open.forEach(w => { const name = w.exe.replace(/\.exe$/i, ""); win.appendChild(chip(name, appIcon({ name, exes: [w.exe] }), w.title ? `${w.exe} · ${w.title}` : w.exe, () => addLayer(name, [w.exe], {}))); });
    }).catch(() => { $("winHint").textContent = "No se pudo leer la lista de ventanas."; });
  } else $("winHint").textContent = "Abre la herramienta con start_studio.py para ver las apps abiertas.";
  $("addOverlay").classList.add("show");
}
function closeAdd() { $("addOverlay").classList.remove("show"); }
$("addCancel").addEventListener("click", closeAdd);
$("addOverlay").addEventListener("mousedown", e => { if (e.target === $("addOverlay")) closeAdd(); });
$("btnNewLayer").addEventListener("click", () => {
  const exe = $("newExe").value.trim().toLowerCase();
  if (!exe) return toast("Escribe el nombre del programa (ej. premiere.exe)", true);
  addLayer($("newName").value.trim() || exe.replace(/\.exe$/, ""), [exe.endsWith(".exe") ? exe : exe + ".exe"], {});
  $("newExe").value = ""; $("newName").value = "";
});

document.querySelectorAll("[data-win]").forEach(b => b.addEventListener("click", () => api("/api/window", { action: b.dataset.win }).catch(() => toast("No se pudo cambiar la ventana", true))));

// ---------- Motor: estado en vivo ----------
const SELF_EXE = /^(reviendocker|python|pythonw|msedgewebview2)\.exe$/i;
let lastOther = "";
function renderSuggest() {
  const b = $("appSuggest"), known = lastOther && S.layers.some(l => l.exes.includes(lastOther.toLowerCase()));
  b.hidden = !lastOther || known;
  if (!b.hidden) $("appSuggestText").textContent = `Crear atajos para ${lastOther}`;
}
$("appSuggest").addEventListener("click", () => { const exe = lastOther.toLowerCase(); addLayer(exe.replace(/\.exe$/, ""), [exe], {}); });
function updateEngineUI(st) {
  const pill = $("enginePill");
  if (st && st.desktop !== undefined) { API.desktop = st.desktop; $("winctl").hidden = !st.desktop; }
  if (st && st.active_mode !== undefined && st.active_mode !== liveMode) { liveMode = st.active_mode; if (S.mode === "modes") renderModes(); }
  let cls = "bad", text;
  if (!API.ok) text = "Motor sin conectar";
  else if (st && !st.platform_ok) text = "Solo Windows";
  else if (st && st.running) { cls = "ok"; text = "Motor activo" + (liveMode >= 0 && S.modes[liveMode] ? " · " + S.modes[liveMode].name : ""); }
  else if (!st) { cls = ""; text = "Iniciando…"; }
  else text = "Motor detenido";
  pill.className = "pill " + cls; $("engineText").textContent = text; pill.title = text; updateSys();
  const err = $("engineErr"); err.hidden = !(st && st.error); err.textContent = st && st.error ? st.error : "";
  if (st && st.active_exe !== undefined) {
    const exe = st.active_exe || "";
    if (exe && !SELF_EXE.test(exe)) lastOther = exe;      // al volver a RevienDocker se conserva la última app real
    $("activeApp").textContent = lastOther || "—";
    $("liveApp").style.opacity = exe && SELF_EXE.test(exe) ? 0.6 : 1;
    document.querySelectorAll(".layer-tab[data-layer]").forEach(t => t.classList.toggle("is-live", t.dataset.layer === st.active_layer && st.active_layer !== "base"));
    renderSuggest();
  } else if (!API.ok) $("activeApp").textContent = "—";
}
setInterval(() => {
  if (!API.ok || document.hidden) return;
  api("/api/status").then(updateEngineUI).catch(() => { API.ok = false; updateEngineUI(null); });
}, 1500);

// ---------- Grabación real (teclado + ratón) ----------
// En la app de escritorio el teclado lo captura el motor nativo (hook de Windows: sirve Alt+Tab, Win, Esc…) y llega por /api/record.
// En un navegador se usa pantalla completa + Keyboard Lock como alternativa. El ratón siempre se lee en esta ventana.
let rec = null;
const recAction = r => (r.btn || r.wheel) ? Ms(r.mod, r.btn, r.wheel, 1) : K(r.mod, r.key);
function updateRecStatus() {
  const s = $("recStatus");
  if (s) { s.classList.remove("warn"); s.textContent = ""; }
}
function recWarn(text) { const s = $("recStatus"); s.textContent = text; s.classList.add("warn"); }
const recRender = () => renderChips($("recChips"), recAction(rec));
const recSnap = () => ({ mod: rec.mod, key: rec.key, btn: rec.btn, wheel: rec.wheel });
function recApply(n) {
  if (popcount(n.mod) + ((n.key || n.btn || n.wheel) ? 1 : 0) > MAX_KEYS) return recWarn(`Máximo ${MAX_KEYS} teclas en total`);
  Object.assign(rec, { mod: n.mod, key: n.key, btn: n.btn, wheel: n.wheel, got: true });
  updateRecStatus(); recRender();
}
function recKey(down, id, modBit, hid) {  // origen común: DOM o motor nativo
  if (!rec) return;
  if (!down) { rec.held.delete(id); return recMaybeFinish(); }
  rec.held.add(id);
  const n = recSnap();
  if (modBit) n.mod |= modBit;
  else {
    if (!hid) return recWarn("Tecla no soportada. Usa «Atajos del sistema».");
    n.key = hid; n.btn = 0; n.wheel = 0;
  }
  recApply(n);
}
function onKeyDown(e) {
  e.preventDefault(); e.stopPropagation();
  if (e.repeat) return;
  const m = MOD_BITS.find(x => x.dom.includes(e.code));
  recKey(true, "k" + e.code, m && m.bit, DOM_TO_HID[e.code]);
}
function onKeyUp(e) { e.preventDefault(); e.stopPropagation(); recKey(false, "k" + e.code); }
const BTN_BIT = { 0: 1, 1: 4, 2: 2, 3: 8, 4: 16 };
function onMouseDown(e) {
  if (e.target.closest?.("#recCancel")) return;
  e.preventDefault(); e.stopPropagation();
  rec.held.add("m" + e.button);
  const n = recSnap(); n.btn = BTN_BIT[e.button] || 0; n.key = 0; n.wheel = 0;
  recApply(n);
}
function onMouseUp(e) { if (e.target.closest?.("#recCancel")) return; e.preventDefault(); e.stopPropagation(); rec.held.delete("m" + e.button); recMaybeFinish(); }
function onWheel(e) {
  e.preventDefault(); e.stopPropagation();
  const n = recSnap(); n.wheel = e.deltaY < 0 ? 1 : -1; n.btn = 0; n.key = 0;
  recApply(n);
  clearTimeout(rec.timer); rec.timer = setTimeout(recMaybeFinish, 350);
}
const stopEvt = e => { if (!e.target.closest?.("#recCancel")) { e.preventDefault(); e.stopPropagation(); } };
const REC_LISTENERS = [["keydown", onKeyDown], ["keyup", onKeyUp], ["mousedown", onMouseDown], ["mouseup", onMouseUp],
  ["wheel", onWheel], ["contextmenu", stopEvt], ["auxclick", stopEvt], ["click", stopEvt]];
function recMaybeFinish() { if (rec && rec.got && rec.held.size === 0) recFinish(); }
function recFinish() {
  const a = recAction(rec);
  recEnd();
  if (!hasMain(a) && !a.mod) return;
  setAction(a); toast("Asignado: " + textOf(a));
}
function recEnd() {
  if (!rec) return;
  REC_LISTENERS.forEach(([t, f]) => window.removeEventListener(t, f, true));
  clearTimeout(rec.timer); clearInterval(rec.poll);
  $("recOverlay").classList.remove("show");
  const { native, fs } = rec; rec = null;
  if (native) api("/api/record", { action: "stop" }).catch(() => {});
  try { if (navigator.keyboard && navigator.keyboard.unlock) navigator.keyboard.unlock(); } catch (_) {}
  if (fs && document.fullscreenElement) document.exitFullscreen().catch(() => {});
}
async function pollRec() {
  const me = rec;
  if (!me || me.busy) return;
  me.busy = true;
  try {
    const r = await api("/api/record?since=" + me.since);
    if (rec !== me) return;
    me.since = r.next;
    r.events.forEach(ev => recKey(!ev.up, "n" + ev.id, ev.mod, ev.hid));
    if (!r.active && rec === me) recEnd();   // el motor cortó la captura (tiempo máximo)
  } catch (_) {} finally { me.busy = false; }
}
async function recStart() {
  if (rec) return;
  const me = rec = { mod: 0, key: 0, btn: 0, wheel: 0, held: new Set(), got: false, fs: false, locked: false, native: false, timer: null, poll: null, since: 0, busy: false };
  $("recTitle").textContent = "Grabando · " + TARGET_NAME[currentTarget];
  $("recOverlay").classList.add("show");
  recRender(); updateRecStatus();
  setTimeout(() => { if (rec === me) REC_LISTENERS.forEach(([t, f]) => window.addEventListener(t, f, { capture: true, passive: false })); }, 0);
  if (API.ok) {
    try { me.native = !!(await api("/api/record", { action: "start" })).ok; } catch (_) {}
    if (rec !== me) { if (me.native) api("/api/record", { action: "stop" }).catch(() => {}); return; }
    if (me.native) { me.poll = setInterval(pollRec, 40); updateRecStatus(); return; }
  }
  const fs = document.documentElement.requestFullscreen ? document.documentElement.requestFullscreen() : Promise.reject();
  fs.then(() => { if (rec === me) me.fs = true; }).catch(() => {})
    .then(() => (rec === me && navigator.keyboard && navigator.keyboard.lock) ? navigator.keyboard.lock().then(() => { if (rec === me) me.locked = true; }) : null)
    .catch(() => {})
    .then(() => { if (rec === me) updateRecStatus(); });
}
$("recCancel").addEventListener("click", recEnd);
document.addEventListener("fullscreenchange", () => { if (rec && rec.fs && !document.fullscreenElement) recEnd(); });
window.addEventListener("blur", () => { if (rec && !rec.native) recEnd(); });

// ---------- Flasheo (WebHID / backend / simulación local) ----------
const REPORT_ID = 0x03;
let hidDevice = null;
function framesToFlash() {
  const frames = [];
  SLOT_ORDER.forEach(k => slotMessages(k, hwAction(k)).forEach(m => frames.push([k, m])));
  frames.push(["LED", msg(0xA1, 1)], ["LED", msg(0xB0, 0x18, S.led_mode)], ["LED", msg(0xAA, 0xA1)]);
  return frames;
}
function devicePill(connected, text) { deviceConnected = connected; $("devicePill").classList.toggle("ok", connected); $("deviceText").textContent = text; $("devicePill").title = text; updateSys(); refreshUI({ quiet: true }); }

// ---------- Ajustes (rueda dentada): estado del teclado y del motor, y buscar el teclado ----------
// El punto de la rueda avisa solo si algo no va bien (ámbar: sin teclado o arrancando; rojo: motor caído).
function updateSys() {
  const eng = $("enginePill").classList, dev = $("devicePill").classList, d = $("sysDot");
  const level = eng.contains("bad") ? "bad" : (!eng.contains("ok") || !dev.contains("ok")) ? "warn" : "";
  d.hidden = !level; d.classList.toggle("bad", level === "bad");
}
function setSys(open) { $("sysMenu").hidden = !open; $("btnSys").setAttribute("aria-expanded", String(open)); $("btnSys").classList.toggle("active", open); }
$("btnSys").addEventListener("click", () => setSys($("sysMenu").hidden));
document.addEventListener("click", e => { if (!$("sysMenu").hidden && !$("sysWrap").contains(e.target)) setSys(false); });
$("sysMenu").addEventListener("click", e => { if (e.target.closest("#btnConnect")) setSys(false); });
async function probeDevice(manual) {
  try {
    const r = await api("/api/device");
    devicePill(r.connected, r.connected ? "Teclado · " + r.name : "Simulador");
    if (manual) toast(r.connected ? "Teclado detectado" : "No se detecta el teclado: sigues en simulador", !r.connected);
  } catch (_) {}
}
$("btnConnect").addEventListener("click", async () => {
  if (API.ok) return probeDevice(true);   // app de escritorio: el backend habla con el USB (hidapi)
  if (!("hid" in navigator)) return logLine("WebHID no disponible en este navegador (usa Chrome/Edge). Sigues en simulador.", "#fbbf24");
  try {
    const [dev] = await navigator.hid.requestDevice({ filters: [{ vendorId: 0x1189, usagePage: 0xFF00 }] });
    if (!dev) return logLine("Ningún dispositivo seleccionado. Sigues en simulador.", "#fbbf24");
    await dev.open();
    hidDevice = dev;
    devicePill(true, "Teclado · " + dev.productName);
    logLine("Conectado a " + dev.productName, "#34d399");
  } catch (err) { logLine("Error WebHID: " + err.message + " · Sigues en simulador.", "#fbbf24"); }
});
function markApplied() {
  S.flashed = hwSig();   // lo último escrito en el teclado (no se puede leer); los atajos ya no pasan por el firmware
  savedSnap = snapOf();
  persist(); refreshUI({ quiet: true });
}
$("btnDiscard").addEventListener("click", () => {
  if (!savedSnap) return;
  try {
    const snap = JSON.parse(savedSnap);
    S.layers = snap.layers; S.modes = snap.modes; S.trigger = snap.trigger;
    closeEditorUI(); collapseAllFolds(); persist(); refreshUI();
    toast("Cambios descartados");
  } catch (_) {}
});
$("btnFlashAll").addEventListener("click", async () => {
  if (hidDevice) {
    for (const [tag, f] of framesToFlash()) {
      await hidDevice.sendReport(REPORT_ID, f);
      logLine(`[TX USB] ${tag}: 03 ${hexOf(f)} ...`, "#34d399");
    }
    markApplied(); toast("Teclado preparado");
    return;
  }
  const payload = {};
  SLOT_ORDER.forEach(k => { const a = hwAction(k); payload[k] = { type: a.type, modifiers: a.mod, hid_code: a.code, wheel: a.wheel, speed: a.speed }; });
  try {
    const r = await api("/api/flash", { mappings: payload, led_mode: S.led_mode });
    if (r.ok === false) return toast("No se pudo escribir en el teclado: " + r.error, true);
    r.logs.forEach(l => logLine(l, "#34d399"));
    if (r.logs.some(l => l.includes("TX USB"))) { markApplied(); toast("Teclado preparado"); }
    else { savedSnap = snapOf(); refreshUI({ quiet: true }); toast("Cambios guardados"); }
  } catch (_) {
    for (const [tag, f] of framesToFlash()) logLine(`[SIMULADOR] ${tag}: 03 ${hexOf(f)} ...`, "#34d399");
  }
});

hydrateIcons();
load().then(() => { refreshUI(); if (API.ok) probeDevice(false); if (API.ok) api("/api/status").then(updateEngineUI).catch(() => {}); else updateEngineUI(null); });
})();
