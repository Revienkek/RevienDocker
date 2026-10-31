# Guía de usuario — RevienDocker

Documento vivo: cada función nueva del proyecto se añade aquí. Última revisión: 2026-10-31.

## 1. Qué es

Un programador para el macropad de 3 teclas + 1 rueda (chip WCH CH57x). El teclado guarda en su propia memoria (EEPROM) qué tecla pulsa cada botón. Esta herramienta construye esas asignaciones y las envía por USB. Una vez grabadas, el teclado las ejecuta solo, sin software abierto.

## 2. Arrancar

**Como programa (recomendado):** abre el acceso directo «RevienDocker» del escritorio (o `dist\RevienDocker.exe`). Es una ventana propia, sin marco de Windows: arriba tiene su minimizar, maximizar y cerrar.
- En modo **Directo**, cerrar sale del programa (el teclado ya lleva todo dentro).
- En modo **Inteligente**, cerrar la oculta en la bandeja (junto al reloj) y el motor sigue activo. Salir del todo: clic derecho en su icono → Salir.
- Si ya está abierto, avisa en vez de abrir otro.

**En desarrollo:**

```bash
python start_studio.py
```

Abre `http://127.0.0.1:8765/index.html`. También vale abrir `index.html` con doble clic (sin backend Python).

## 2b. Los dos modos

| | 🎯 Directo | 🧠 Inteligente |
|---|---|---|
| Dónde vive la lógica | Dentro del teclado (EEPROM) | En este programa, en tu PC |
| Necesita el programa abierto | No | Sí (`python start_studio.py`) |
| Qué flasheas | Tus atajos | Teclas fantasma F13–F18 (una sola vez) |
| Qué puedes hacer | Teclas, ratón, multimedia | Todo lo anterior + OBS + **capas por app** |

**Modo inteligente, paso a paso**
1. Pulsa la tarjeta «Inteligente». Aparece la barra de capas y los ajustes.
2. Flashea una vez («Flashear teclas fantasma»). El teclado pasa a emitir F13–F18 y este programa las intercepta (ninguna app las ve).
3. **Capa Base:** lo que hace cada botón sin tecla de activación.
4. **＋ Añadir app:** elige una plantilla (OBS Studio, Navegador, Spotify), una app abierta ahora o escribe el `.exe`. Esa capa se usa cuando mantienes **Shift** (o Ctrl/Alt, a tu elección) y pulsas un botón con esa app en primer plano.
5. Un botón vacío en una capa de app usa la acción de la Base. Una app sin capa también.
6. «App en primer plano» muestra en vivo qué detecta el programa; la pestaña de la capa se enciende en verde al coincidir. Cambia de ventana y míralo.
7. **▶ Probar** ejecuta la acción en este PC tras 3 segundos (cambia antes a la ventana donde quieras probarla). Sirve para ensayar sin el teclado.

Qué pasa por dentro: el motor es un hook de teclado que solo reacciona a F13–F18 y no consume nada mientras no pulsas. La acción se ejecuta con Shift/Ctrl/Alt «soltado» y se restaura al terminar, para que la app no vea Shift+tu atajo.

### OBS Studio (acciones nativas)
Activa en OBS: Herramientas → Ajustes del servidor WebSocket → Habilitar. Pon host, puerto y contraseña en «Elegir a mano → OBS → Conexión». Acciones: escena siguiente/anterior, ir a una escena, mostrar/ocultar una fuente de la escena actual (ej. «Fondo negro»), silenciar un micro, subir/bajar su volumen (la velocidad son dB por clic) e iniciar/parar grabación o directo. La plantilla «OBS Studio» y la receta «Volumen del micro (OBS)» lo dejan listo con la entrada `Mic/Aux`; cambia el nombre si tu micro se llama distinto.

## 3. La pantalla

La pantalla se lee de izquierda a derecha: **① elige un botón → ② decide qué hace**. Solo lo imprescindible está a la vista; lo demás está en secciones plegables.

### Cabecera
- **Directo / Inteligente:** el modo de trabajo (ver sección 2b).
- **Píldora del teclado:** ámbar = simulador; verde = teclado real conectado. En modo Inteligente aparece otra con el estado del motor.
- **Enchufe:** busca el teclado de nuevo.
- **Flashear:** escribe la configuración en el teclado. Un **punto rojo** significa que lo que ves aún no está escrito en el teclado conectado. En simulador solo escribe las tramas en la consola.
- **Minimizar / maximizar / cerrar:** la ventana es propia (solo en el programa de escritorio).
- **Redimensionar:** en el programa de escritorio, arrastra cualquier borde o esquina de la ventana (el cursor cambia a flecha de redimensionar). Tamaño mínimo 820 × 560; con ventana maximizada no se redimensiona.

### Panel 1: el teclado
- **KEY 1/2/3:** las tres teclas mecánicas. Muestran la acción asignada (ej. `Ctrl+Shift+F13`).
- **↺ / ↻:** giro de la rueda a izquierda / derecha.
- **Círculo central:** clic del pomo.
- Pulsa cualquiera para seleccionarla (borde morado); el título muestra `EDITANDO: ...`.
- **Presets rápidos:** reemplazan las 6 asignaciones de golpe.
  - Fantasma NikaDeck: F13–F18, teclas que ningún programa usa, ideales para interceptarlas con otro software.
  - Multimedia + Volumen: anterior/play/siguiente, volumen y mute.
  - OBS + Mic Mute: Ctrl+Shift+F13/F14/F15, volumen y Ctrl+M en el clic.
  - Dev / Git + Zoom: Ctrl+C, Ctrl+V, Enter, rueda como scroll y Espacio en el clic.
- **Iluminación LED:** apagado, fijo, respiración o reactivo. Se envía junto al resto al flashear.

### Panel 2: qué hace
Al elegir un botón del panel izquierdo solo se selecciona; no empieza a grabar. Aquí ves qué tiene asignado y decides cómo cambiarlo.

- **Asignado ahora:** la acción actual en chips (`Ctrl + Shift + Z`), con su tipo y el contador `n / 3 teclas`. Si lleva velocidad, aparece un selector.
- **⏺ Grabar con mi teclado y ratón:** abre una ventana de grabación. Pulsa la combinación, haz clic con cualquier botón del ratón (izquierdo, derecho, central, atrás, adelante) o mueve la rueda. Se guarda sola al soltar. Se puede combinar con Ctrl/Shift/Alt/Win (ej. Ctrl + clic derecho, Ctrl + rueda).
  - En el programa de escritorio la captura de teclado la hace el motor nativo (hook de Windows): Alt+Tab, Win y similares se graban sin que el PC los ejecute. Tiene un tiempo máximo de 20 s por seguridad. Para salir sin guardar: «Cancelar».
  - En un navegador (desarrollo) se usa pantalla completa + bloqueo de teclado como alternativa menos fiable.
  - **Ctrl+Alt+Supr es imposible de capturar** (lo trata el propio Windows). Para eso y para los demás atajos del sistema están los «Atajos del sistema».
- **Límite:** 1 tecla, o combinación de 2 o 3 en total, contando los modificadores. Ctrl+C = 2, Ctrl+Shift+F13 = 3. Una combinación es modificadores + una sola tecla normal (o un botón/rueda del ratón).
- **Atajos listos:** Alt+Tab, Win+Tab, Alt+F4, Win+D, Win+L, Win+E, Win+V, Win+Shift+S, Ctrl+Alt+Supr, Ctrl+Shift+Esc, Win+., Alt+Esc. Un clic y se asignan sin grabar.
- **Elegir a mano:** pestañas Teclado (lista completa), Ratón (los 5 botones y rueda ↑/↓) y Multimedia, con los modificadores arriba.
- **Borrar:** deja el botón sin asignar.
- **Consola de tramas:** el paquete de cada cambio y de cada flasheo. Lo más reciente va arriba.

### Recetas de rueda
Al elegir ↺, ↻ o el clic del pomo aparece arriba el cuadro de recetas. Un clic en una receta configura giro izquierdo, giro derecho y pulsación a la vez.

| Receta | Giro | Pulsar |
|---|---|---|
| 🔊 Volumen | Vol − / Vol + | Mute |
| 📜 Scroll | Rueda ↑ / ↓ | Clic central (autoscroll) |
| 🔍 Zoom | Ctrl + rueda | Ctrl+0 (100%) |
| 🗂 Pestañas | Ctrl+Shift+Tab / Ctrl+Tab | Ctrl+Shift+T (reabrir) |
| 🎞 Línea de tiempo | ← / → | Espacio |
| ↩ Deshacer / Rehacer | Ctrl+Z / Ctrl+Y | Ctrl+S |
| ⏭ Pistas | Anterior / Siguiente | Play/Pausa |
| 🖌 Tamaño de pincel | [ / ] | sin cambios |

- **Velocidad de giro:** Fino ×1, Normal ×2, Rápido ×3, Turbo ×5. Es cuánto avanza cada «clic» de la rueda. Aplica a volumen (repite la orden) y a scroll/zoom (valor de rueda). Solo se activa si la receta lo admite.
- **⇄ Invertir sentido:** intercambia giro izquierdo y derecho.
- Después de aplicar una receta puedes retocar cualquier parte con grabar o a mano.

## 4. Cómo funciona por dentro

1. La interfaz guarda todo (modo, capas, acciones) en el navegador y, con el servidor activo, en `studio.json`. Se recupera al reabrir.
2. Al flashear genera una secuencia de paquetes de 65 bytes: **Unlock → 6 escrituras → LED → Commit**.
3. Los envía por uno de estos caminos, en este orden:
   1. WebHID, si pulsaste «Conectar».
   2. El backend Python (`POST /api/flash`), que usa `hidapi` si hay teclado y simula si no.
   3. Simulación dentro del navegador, si abriste el HTML sin servidor.
4. Formatos: tecla `03 <slot> 11 01 01 <mod> <código>`; multimedia `03 <slot> 12 <lo> <hi> <repeticiones>`; ratón `03 <slot> 13 <mod> <botones> <rueda con signo>`.

Slots: KEY_1 `01`, KEY_2 `02`, KEY_3 `03`, rueda izq. `0D`, clic `0E`, rueda der. `0F`.

## 5. Flujo recomendado

1. Elige un preset o ajusta botón a botón.
2. Revisa las tramas en la consola.
3. Con el teclado: «Conectar WebHID», selecciona el dispositivo, «Flashear».
4. Prueba pulsando las teclas en un editor de texto.

## 6. Primer uso con el teclado real (mañana)

- Hazlo primero con el preset Fantasma (F13–F18): es el menos peligroso si algo falla.
- Las tramas no están verificadas contra el firmware. Si el teclado no responde o hace algo raro, anótalo aquí en «Problemas conocidos».
- Windows puede no listar la interfaz `0xFF00` en WebHID. Si pasa, usa el backend Python (`pip install hidapi`).

## 7. Limitaciones actuales

- No hay botón para exportar/importar configuración (puedes copiar `studio.json`).
- El modo inteligente solo funciona en Windows y con el programa abierto (en la bandeja basta).
- Nada de esto se ha probado todavía con el teclado real ni con OBS real (solo con simuladores y pruebas automáticas).
- Alt como tecla de activación puede abrir el menú de algunas apps al soltarla; Shift es lo más limpio.
- Si cambias de capa o de ventana con un botón pulsado, la acción usa la app que esté activa en ese instante.
- «Escena siguiente/anterior» asume el orden de la lista de OBS; si sale al revés, cámbialo en el código (`studio_engine.py`).
- Solo se programa la capa 1.
- Un botón no puede llevar dos teclas normales a la vez (A+B) ni una secuencia de pasos.
- «Mute rápido» o «llegar al final» (que la rueda baje hasta silenciar) no se puede hacer en el chip: gira un paso por clic. Lo más cercano es la velocidad Turbo y la pulsación = Mute.

## 8. Problemas conocidos

_(vacío; se rellena al probar con el hardware)_

## 9. Historial

| Fecha | Cambio |
|---|---|
| 2026-10-31 | v0.02: icono nuevo (`assets/ICON.jpg` → `icon.png/.ico`), título metálico en Doris PP, interfaz en Expressway, esquinas suaves (nunca cuadradas) y documento de diseño `DISEÑO.md`. |
| 2026-10-31 | v0.01: ventana redimensionable por bordes y esquinas (zonas propias, la ventana sin marco no tenía borde nativo), diseño que se adapta de 820 a 1400 px (flujo del modo Inteligente sin saltos de fila, dos columnas pasan a una en anchuras medianas), botones de ventana visibles también al arrancar en modo Directo, lista blanca de acciones en `/api/window`. |
| 2026-10-31 | Renombrado a **RevienDocker**: icono nuevo (R · v · D), ventana propia sin marco y compacta, iconos Lucide, interfaz reducida con flujo visual, grabación nativa de teclado, aviso de «sin flashear». |
| 2026-10-31 | Aplicación de escritorio: `RevienDocker.exe` con ventana, bandeja, instancia única y USB por hidapi. |
| 2026-10-31 | Rediseño completo (studio.css / studio.js), modo Inteligente con capas por app, tecla de activación, motor Windows, OBS WebSocket nativo, persistencia, botón Probar. |
| 2026-10-31 | Grabación real con paso intermedio, captura total en Chrome/Edge, atajos listos, ratón completo, recetas de rueda y velocidad. |
| 2026-10-31 | Editor de botón con captura de teclado (1 a 3 teclas), pestañas y catálogo completo de teclas. |
| 2026-10-31 | Proyecto recuperado de Drive; modo simulador, LED, preset Dev, WebHID, pruebas. |
