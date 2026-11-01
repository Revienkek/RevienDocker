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
const defaultState = () => ({ mode: "direct", trigger: "shift", led_mode: 1, flashed: "", applied: null, obs: { host: "127.0.0.1", port: 4455, password: "" },
  layers: [{ id: "base", name: "Base", exes: [], actions: defaultBase() }] });
const LS_KEY = "botonera.studio.v2";
let S = defaultState();
let layerId = "base", currentTarget = "KEY_1", viewTab = "keyboard", knobSpeed = 1;
const API = { ok: false, desktop: false };
let deviceConnected = false;
const layer = () => S.layers.find(l => l.id === layerId) || S.layers[0];
const isApp = () => layer().id !== "base";
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
  s.applied = s.applied && typeof s.applied === "object" ? s.applied : null;
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
}

// ---------- Utilidades de UI ----------
const hexOf = f => Array.from(f).slice(0, 11).map(x => x.toString(16).padStart(2, "0").toUpperCase()).join(" ");
const hexConsole = $("hexConsole");
function logLine(text, color) {
  const d = document.createElement("div");
  if (color) d.style.color = color;
  d.textContent = text; hexConsole.prepend(d);
}
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
const hwAction = slot => {
  const a = S.layers[0].actions[slot];
  return S.mode === "smart" || isWheelVolume(slot, a) ? K(0, kc(GHOST[slot])) : (a && a.type !== "obs" ? a : EMPTY);
};
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
const INFO = {
  direct: () => ["target", "Los atajos se guardan dentro del teclado y funcionan en cualquier PC."],
  smart: t => ["brain", `Sin modificador se usa la acción base; mantén ${t} para usar la acción de la app activa. El motor debe estar abierto.`],
  modes: () => ["shapes", "Próximamente: perfiles y modos de trabajo personalizados."]
};
const hwSig = () => SLOT_ORDER.map(k => slotMessages(k, hwAction(k)).map(hexOf).join("/")).join("|") ;
let wasKnob = false;
const layerLabel = () => layer().id === "base" ? "Todas las apps" : layer().name;
function refreshUI(opts = {}) {
  const smart = S.mode === "smart", trig = TRIGGERS[S.trigger];
  document.querySelectorAll(".modes button").forEach(c => { const on = c.dataset.mode === S.mode; c.classList.toggle("active", on); c.setAttribute("aria-checked", on); });
  const [ico, txt] = (INFO[S.mode] || INFO.direct)(trig);
  $("infoText").innerHTML = txt; $("infoIcon").innerHTML = ic(ico);
  const dirty = deviceConnected && S.flashed !== hwSig();
  $("flashText").textContent = smart ? "Preparar teclado" : "Aplicar cambios";
  $("btnFlashAll").title = smart ? "Escribe en el teclado las teclas fantasma F13–F18 (solo hace falta una vez)" : "Escribe en el teclado lo que ves en pantalla";
  $("flashDot").hidden = !dirty;
  $("btnDiscard").hidden = !(dirty && !smart && S.applied);
  if (!smart && deviceConnected && !S.applied) { $("infoText").textContent = "El teclado no se puede leer: no sé qué lleva dentro. Pulsa «Aplicar cambios» para que coincida con esta pantalla."; $("infoIcon").innerHTML = ic("info"); }
  else if (!smart && ["KNOB_CCW", "KNOB_CW"].some(k => isWheelVolume(k, S.layers[0].actions[k]))) {
    $("infoText").textContent = "El volumen ajustable necesita RevienDocker abierto o en la bandeja. El resto funciona directamente en el teclado.";
    $("infoIcon").innerHTML = ic("info");
  }
  if (!smart) layerId = "base";
  $("smartCard").hidden = !smart; $("smartRule").hidden = !smart; $("tabObs").hidden = !smart;
  if (!smart && viewTab === "obs") viewTab = "keyboard";
  $("ledToggle").setAttribute("aria-checked", S.led_mode !== 0);
  $("ledToggleText").textContent = S.led_mode !== 0 ? "Encendida" : "Apagada";
  $("ledNote").textContent = (LED_INFO[S.led_mode] || "Modo sin documentar.") + " El color lo decide el propio teclado: ni el programa del fabricante permite elegirlo.";
  $("ledModes").querySelectorAll("button").forEach(b => b.classList.toggle("active", +b.dataset.led === S.led_mode));
  $("winClose").title = smart || S.volume_bridge ? "Cerrar a la bandeja (el motor sigue activo)" : "Cerrar";

  if (smart) {
    renderLayers();
    renderSeg($("triggerSeg"), S.trigger, v => { S.trigger = v; persist(); refreshUI(); }, Object.entries(TRIGGERS));
    renderRule();
    $("layerEdit").hidden = !isApp();
    if (isApp()) { setVal($("layerName"), layer().name); setVal($("layerExes"), layer().exes.join(", ")); }
  }

  SLOT_ORDER.forEach(k => {
    const a = shown(k), box = document.querySelector(`[data-target="${k}"]`);
    box.classList.toggle("inherit", isApp() && !own(k));
    const text = a ? textOf(a) : "—";
    $("lbl_" + k).textContent = (k === "KNOB_CCW" ? "↺ " : k === "KNOB_CW" ? "↻ " : "") + text;
  });

  const a = cur(), isKnob = currentTarget.startsWith("KNOB"), inherited = isApp() && !own(currentTarget);
  $("selectedLabel").textContent = $("editor").hidden ? "" : TARGET_NAME[currentTarget] + (smart ? ` · ${layerLabel()}` : "");
  $("comboCount").textContent = (a.type === "media" || a.type === "obs") ? "" : `${countOf(a)} / ${MAX_KEYS} teclas`;
  $("curMeta").textContent = TYPE_NAME[a.type];
  $("curCard").classList.toggle("inherited", inherited);
  $("curLabel").textContent = inherited ? "Sin definir · usa la Base" : "Asignado";
  $("btnClear").title = isApp() ? "Quitar (usar la Base)" : "Borrar";
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

  $("knobTools").hidden = !isKnob;
  if (isKnob !== wasKnob) { $("knobTools").open = isKnob; wasKnob = isKnob; }   // al elegir la rueda se abre sus recetas; el resto se cierra solo
  if (isKnob) {
    const box = $("recipes"); box.innerHTML = "";
    const mapOf = r => `↺ ${textOf(r.ccw)} · ↻ ${textOf(r.cw)}${r.press ? " · ● " + textOf(r.press) : ""}`;
    RECIPES.filter(r => smart || !r.obs).forEach(r => {
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

  document.querySelectorAll(".tab").forEach(t => t.classList.toggle("active", t.dataset.tab === viewTab));
  ["keyboard", "mouse", "media", "obs"].forEach(t => $("m-" + t).classList.toggle("show", t === viewTab));
  $("modsRow").hidden = viewTab === "media" || viewTab === "obs";
  document.querySelectorAll(".mod-btn").forEach(btn => btn.classList.toggle("active", modsOf(a) & parseInt(btn.dataset.bit, 10) ? true : false));
  $("keySelect").value = a.type === "keyboard" ? a.code : 0;
  document.querySelectorAll("#m-mouse .opt").forEach(o => {
    const bit = parseInt(o.dataset.bit, 10), w = parseInt(o.dataset.wheel, 10);
    o.classList.toggle("active", a.type === "mouse" && (w ? a.wheel === w : a.code === bit && !a.wheel));
  });
  document.querySelectorAll("#m-media .opt").forEach(o => o.classList.toggle("active", a.type === "media" && a.code === parseInt(o.dataset.code, 10)));
  document.querySelectorAll("#obsOps .opt").forEach(o => o.classList.toggle("active", a.type === "obs" && a.op === o.dataset.op));
  const od = a.type === "obs" ? OBS_BY_OP[a.op] : null;
  $("obsTargetRow").hidden = !(od && od.needs);
  if (od && od.needs) { $("obsTargetLabel").textContent = od.needs; setVal($("obsTarget"), a.target || ""); }
  setVal($("obsHost"), S.obs.host); setVal($("obsPort"), S.obs.port); setVal($("obsPass"), S.obs.password);

  if (!opts.quiet) slotMessages(currentTarget, hwAction(currentTarget)).slice(1, -1).forEach(m => logHex(`PREVIEW [${currentTarget}]`, m));
}
function logHex(tag, bytes) { logLine(`[${new Date().toLocaleTimeString()}] ${tag}: 03 ${hexOf(bytes)} ...`); }

function renderLayers() {
  const bar = $("layerWrap"); bar.innerHTML = "";
  S.layers.forEach(l => {
    const b = el("button", "layer-tab" + (l.id === layerId ? " active" : ""));
    b.innerHTML = ic(l.id === "base" ? "layers" : "app-window") + `<span></span><span class="live"></span>`;
    b.children[1].textContent = l.id === "base" ? "Todas las apps" : l.name; b.dataset.layer = l.id;
    b.title = l.id === "base" ? "Lo que hace cada botón al pulsarlo solo, en cualquier app" : `Se usa con ${TRIGGERS[S.trigger]} mantenida en: ${l.exes.join(", ") || "(sin programa)"}`;
    b.addEventListener("click", () => { if (l.id !== layerId) { layerId = l.id; swapFx(); refreshUI(); } });
    bar.appendChild(b);
  });
  const add = el("button", "layer-tab add"); add.innerHTML = ic("plus") + "<span>Añadir app</span>"; add.title = "Atajos propios para otra app";
  add.addEventListener("click", openAdd);
  bar.appendChild(add);
}
function renderRule() {
  const t = TRIGGERS[S.trigger], l = layer();
  const kbd = s => `<kbd>${s}</kbd>`, plus = ic("plus"), arrow = ic("arrow-right");
  $("rule").innerHTML = l.id === "base"
    ? `${kbd("Botón")}${arrow}<b>cualquier app</b><span class="why">Pulsa el botón solo. Es también lo que hace en una app que no tenga atajos propios.</span>`
    : `${kbd(t)}${plus}${kbd("Botón")}${arrow}<b></b><span class="why">Mantén ${t} mientras pulsas el botón, con esta app en primer plano.</span>`;
  if (l.id !== "base") $("rule").querySelector("b").textContent = l.name;
}
function setAction(a) { layer().actions[currentTarget] = a; persist(); refreshUI(); }

// ---------- Controles estáticos ----------
(function build() {
  const none = el("option", "", "— sin tecla (solo modificadores) —"); none.value = 0;
  $("keySelect").appendChild(none);
  const groups = {};
  KEYS.forEach(k => {
    if (!groups[k.group]) { groups[k.group] = document.createElement("optgroup"); groups[k.group].label = k.group; $("keySelect").appendChild(groups[k.group]); }
    const o = el("option", "", k.label); o.value = k.code; groups[k.group].appendChild(o);
  });
  const mk = (parent, text, attrs, fn) => {
    const b = el("button", "opt", text);
    Object.entries(attrs).forEach(([k, v]) => b.dataset[k] = v);
    b.addEventListener("click", fn); parent.appendChild(b);
  };
  const tryMouse = (btn, wheel) => {
    const a = cur(), mod = modsOf(a);
    if (popcount(mod) + 1 > MAX_KEYS) return toast("Máximo 3 teclas en total", true);
    setAction(Ms(mod, btn, wheel, speedOf(a)));
  };
  MOUSE_BTNS.forEach(b => mk($("m-mouse"), b.label, { bit: b.bit, wheel: 0 }, () => tryMouse(b.bit, 0)));
  mk($("m-mouse"), "Rueda ↑ (scroll arriba)", { bit: 0, wheel: 1 }, () => tryMouse(0, 1));
  mk($("m-mouse"), "Rueda ↓ (scroll abajo)", { bit: 0, wheel: -1 }, () => tryMouse(0, -1));
  MEDIA.forEach(m => mk($("m-media"), m.label, { code: m.code }, () => setAction(M(m.code, speedOf(cur())))));
  OBS_OPS.forEach(o => mk($("obsOps"), o.label, { op: o.op }, () => {
    const a = cur();
    setAction(O(o.op, a.type === "obs" && OBS_BY_OP[a.op].needs === o.needs ? a.target : (o.def || ""), o.speed ? speedOf(a) : 1));
  }));
  LIB.forEach(([name, mod, dom]) => {
    const b = el("button", "", name);
    b.addEventListener("click", () => { setAction(K(mod, kc(dom))); toast("Asignado: " + name); });
    $("lib").appendChild(b);
  });
})();

// ---------- Eventos de la interfaz ----------
document.querySelectorAll("[data-target]").forEach(t => {
  t.addEventListener("click", () => {
    document.querySelectorAll("[data-target]").forEach(n => n.classList.remove("selected"));
    t.classList.add("selected");
    currentTarget = t.dataset.target;
    $("editor").hidden = false;
    knobSpeed = cur().speed || 1;
    viewTab = cur().type;
    if (!currentTarget.startsWith("KNOB")) $("manualTools").open = true;
    refreshUI();
  });
});
$("closeEditor").addEventListener("click", () => {
  $("editor").hidden = true;
  document.querySelectorAll("[data-target]").forEach(n => n.classList.remove("selected"));
  $("selectedLabel").textContent = "";
});
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
document.querySelectorAll(".mod-btn").forEach(b => b.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); b.click(); } }));
document.querySelectorAll(".modes button").forEach(c => c.addEventListener("click", () => {
  if (S.mode === c.dataset.mode) return;
  S.mode = c.dataset.mode; persist(); refreshUI(); updateEngineUI(null);
  if (S.mode === "smart") toast(API.ok ? "Modo inteligente: flashea una vez las teclas fantasma" : "El modo inteligente necesita la app RevienDocker abierta", !API.ok);
}));
document.querySelectorAll(".tab").forEach(t => t.addEventListener("click", () => { viewTab = t.dataset.tab; refreshUI({ quiet: true }); }));
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
$("keySelect").addEventListener("change", e => setAction(K(modsOf(cur()), parseInt(e.target.value, 10))));
document.querySelectorAll(".mod-btn").forEach(btn => btn.addEventListener("click", () => {
  const a = cur();
  const base = (a.type === "media" || a.type === "obs") ? (viewTab === "mouse" ? Ms(0, 0) : K(0, 0)) : a;
  const mod = base.mod ^ parseInt(btn.dataset.bit, 10);
  if (popcount(mod) + (hasMain(base) ? 1 : 0) > MAX_KEYS) return toast("Máximo 3 teclas en total", true);
  setAction({ ...base, mod });
}));
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
    note: "Son teclas poco habituales: no hacen nada por sí solas. Asígnalas a acciones en otra app. F16 y F17 también se usan para el volumen ajustable de RevienDocker.",
    actions: () => ({ KEY_1: F(13), KEY_2: F(14), KEY_3: F(15), KNOB_CCW: F(16), KNOB_PRESS: F(18), KNOB_CW: F(17) }) }
];
let selectedPreset = null;
PRESETS.forEach(p => {
  const b = el("button", "preset-card"); b.dataset.preset = p.id;
  b.innerHTML = ic(p.icon) + "<span><strong></strong><small></small></span>";
  b.querySelector("strong").textContent = p.name; b.querySelector("small").textContent = p.desc;
  b.addEventListener("click", () => {
    selectedPreset = p;
    document.querySelectorAll(".preset-card").forEach(card => card.classList.toggle("active", card === b));
    $("presetTitle").textContent = p.name; $("presetDescription").textContent = p.desc;
    $("presetNote").textContent = p.note || "Se reemplazarán las seis acciones de la capa seleccionada. Después puedes personalizarlas.";
    const mapping = $("presetMapping"); mapping.innerHTML = "";
    const actions = p.actions();
    SLOT_ORDER.forEach(slot => { const cell = el("div"), label = el("small", "", TARGET_NAME[slot]), value = el("strong", "", textOf(actions[slot])); cell.append(label, value); mapping.appendChild(cell); });
    $("presetPreview").hidden = false;
  });
  $("presets").appendChild(b);
});
$("applyPreset").addEventListener("click", () => {
  if (!selectedPreset) return;
  const dest = layerLabel();
  if (!window.confirm(`La plantilla «${selectedPreset.name}» reemplazará las seis acciones de «${dest}». ¿Continuar?`)) return;
  layer().actions = selectedPreset.actions(); persist(); refreshUI(); toast(`Plantilla aplicada a ${dest}`);
});

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
function openAdd() {
  const tpl = $("tplList"); tpl.innerHTML = "";
  TEMPLATES.forEach(t => {
    const b = el("button"); b.appendChild(el("span", "", t.name)); b.appendChild(el("small", "", t.desc));
    b.addEventListener("click", () => addLayer(t.name, t.exes, t.actions()));
    tpl.appendChild(b);
  });
  const win = $("winList"); win.innerHTML = ""; $("winHint").textContent = "";
  if (API.ok) {
    api("/api/windows").then(r => {
      if (!r.windows.length) $("winHint").textContent = "No se detectaron ventanas.";
      r.windows.forEach(w => {
        const b = el("button"); b.appendChild(el("span", "", w.exe.replace(/\.exe$/, ""))); b.appendChild(el("small", "", w.title));
        b.addEventListener("click", () => addLayer(w.exe.replace(/\.exe$/, ""), [w.exe], {}));
        win.appendChild(b);
      });
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
document.querySelectorAll("#resize [data-edge]").forEach(h => h.addEventListener("pointerdown", e => {
  if (e.button === 0) api("/api/window", { action: "resize-" + h.dataset.edge }).catch(() => toast("No se pudo cambiar el tamaño", true));
}));
document.querySelector(".titlebar").addEventListener("dblclick", e => { if (API.desktop && e.target.closest(".pywebview-drag-region")) api("/api/window", { action: "maximize" }).catch(() => {}); });

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
  const pill = $("enginePill"), smart = S.mode === "smart";
  if (st && st.desktop !== undefined) { API.desktop = st.desktop; $("winctl").hidden = !st.desktop; $("resize").hidden = !st.desktop; }
  pill.hidden = !smart;
  if (!smart) return;
  let cls = "bad", text;
  if (!API.ok) text = "Motor sin conectar";
  else if (st && !st.platform_ok) text = "Solo Windows";
  else if (st && st.running) { cls = "ok"; text = "Motor activo"; }
  else if (!st) { cls = ""; text = "Iniciando…"; }
  else text = "Motor detenido";
  pill.className = "pill " + cls; $("engineText").textContent = text;
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
  if (!API.ok || S.mode !== "smart" || document.hidden) return;
  api("/api/status").then(updateEngineUI).catch(() => { API.ok = false; updateEngineUI(null); });
}, 1500);

// ---------- Grabación real (teclado + ratón) ----------
// En la app de escritorio el teclado lo captura el motor nativo (hook de Windows: sirve Alt+Tab, Win, Esc…) y llega por /api/record.
// En un navegador se usa pantalla completa + Keyboard Lock como alternativa. El ratón siempre se lee en esta ventana.
let rec = null;
const recAction = r => (r.btn || r.wheel) ? Ms(r.mod, r.btn, r.wheel, 1) : K(r.mod, r.key);
function updateRecStatus() {
  const s = $("recStatus");
  if (rec && (rec.native || (rec.fs && rec.locked))) { s.classList.remove("warn"); s.textContent = "Captura total activa: Alt+Tab y Win incluidos. Solo Ctrl+Alt+Supr es imposible de capturar: usa «Atajos del sistema»."; }
  else { s.classList.add("warn"); s.textContent = "Captura básica: tu PC puede quedarse Alt+Tab o Win. Para esos usa «Atajos del sistema»."; }
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
    if (!hid) return recWarn("Tecla no soportada. Usa «Elegir a mano».");
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
$("btnRecord").addEventListener("click", recStart);
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
function devicePill(connected, text) { deviceConnected = connected; $("devicePill").classList.toggle("ok", connected); $("deviceText").textContent = text; refreshUI({ quiet: true }); }
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
  S.flashed = hwSig();
  S.volume_bridge = S.mode === "direct" && ["KNOB_CCW", "KNOB_CW"].some(k => isWheelVolume(k, S.layers[0].actions[k]));
  if (S.mode === "direct") S.applied = JSON.parse(JSON.stringify(S.layers[0].actions));   // lo último que lleva el teclado (no se puede leer)
  persist(); refreshUI({ quiet: true });
}
$("btnDiscard").addEventListener("click", () => {
  if (!S.applied) return;
  S.layers[0].actions = JSON.parse(JSON.stringify(S.applied));
  persist(); refreshUI(); toast("Cambios descartados: vuelves a lo último que aplicaste");
});
$("btnFlashAll").addEventListener("click", async () => {
  if (S.mode === "direct" && Object.values(S.layers[0].actions).some(a => a.type === "obs"))
    toast("Las acciones de OBS solo funcionan en modo Inteligente: se dejan vacías en el teclado", true);
  if (hidDevice) {
    for (const [tag, f] of framesToFlash()) {
      await hidDevice.sendReport(REPORT_ID, f);
      logLine(`[TX USB] ${tag}: 03 ${hexOf(f)} ...`, "#34d399");
    }
    markApplied(); toast("Cambios aplicados al teclado");
    return;
  }
  const payload = {};
  SLOT_ORDER.forEach(k => { const a = hwAction(k); payload[k] = { type: a.type, modifiers: a.mod, hid_code: a.code, wheel: a.wheel, speed: a.speed }; });
  try {
    const r = await api("/api/flash", { mappings: payload, led_mode: S.led_mode });
    if (r.ok === false) return toast("No se pudo escribir en el teclado: " + r.error, true);
    r.logs.forEach(l => logLine(l, "#34d399"));
    if (r.logs.some(l => l.includes("TX USB"))) { markApplied(); toast("Cambios aplicados al teclado"); }
    else toast("Simulador: no hay teclado conectado, no se escribió nada", true);
  } catch (_) {
    for (const [tag, f] of framesToFlash()) logLine(`[SIMULADOR] ${tag}: 03 ${hexOf(f)} ...`, "#34d399");
  }
});

hydrateIcons();
load().then(() => { refreshUI(); if (API.ok) probeDevice(false); if (API.ok) api("/api/status").then(updateEngineUI).catch(() => {}); else updateEngineUI(null); });
})();
