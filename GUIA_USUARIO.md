# Guía de usuario — RevienDocker

Documento vivo: cada función nueva del proyecto se añade aquí. Última revisión: 2026-11-01.

## 1. Qué es

Un programador para el macropad de 3 teclas + 1 rueda (chip WCH CH57x). El teclado guarda en su propia memoria (EEPROM) qué tecla pulsa cada botón. Esta herramienta construye esas asignaciones y las envía por USB. Una vez grabadas, el teclado las ejecuta solo, sin software abierto.

## 2. Arrancar

**Como programa (recomendado):** abre el acceso directo «RevienDocker» del escritorio (o `dist\RevienDocker.exe`). Es una ventana propia, sin marco de Windows: arriba tiene su minimizar y cerrar. Su tamaño es fijo.
- RevienDocker debe estar abierto o en la bandeja para que el motor ejecute las acciones de los controles.
- En modo **Inteligente**, cerrar la oculta en la bandeja (junto al reloj) y el motor sigue activo. Salir del todo: clic derecho en su icono → Salir.
- En el menú del icono de la bandeja puedes elegir **Minimizar a la bandeja** o **Mostrar RevienDocker**, según esté visible u oculta. El motor continúa activo mientras la app esté en la bandeja.
- Instancia única garantizada: si intentas abrir RevienDocker mientras ya está en marcha (o minimizado/oculto en la bandeja), se despierta y se trae al frente la ventana activa en lugar de acumular procesos e iconos duplicados.

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
2. Pulsa una vez «Preparar teclado». El teclado pasa a emitir F13–F18 y este programa las intercepta (ninguna app las ve).
3. **Capa Base:** lo que hace cada botón sin tecla de activación.
4. **＋ Añadir app:** elige entre los chips de plantillas (OBS Studio, Navegador, Spotify, WoW Forever), los de apps abiertas ahora (icono y nombre, con desplazamiento si hay muchas) o escribe el `.exe`. Esa capa se usa cuando mantienes **Shift** (o Ctrl/Alt, a tu elección) y pulsas un botón con esa app en primer plano.
5. Un botón vacío en una capa de app usa la acción de la Base. Una app sin capa también.
6. «App en primer plano» muestra en vivo qué detecta el programa; la pestaña de la capa se enciende en verde al coincidir. Cambia de ventana y míralo.
7. **▶ Probar** ejecuta la acción en este PC tras 3 segundos (cambia antes a la ventana donde quieras probarla). Sirve para ensayar sin el teclado.

Qué pasa por dentro: el motor es un hook de teclado que solo reacciona a F13–F18 y no consume nada mientras no pulsas. La acción se ejecuta con Shift/Ctrl/Alt «soltado» y se restaura al terminar, para que la app no vea Shift+tu atajo.

### OBS Studio (acciones nativas)
Activa en OBS: Herramientas → Ajustes del servidor WebSocket → Habilitar. Selecciona OBS Studio en Inteligente y configura host, puerto y contraseña en «Ajustes de esta app → Conexión a OBS». Después, abre el lápiz de un control y elige su acción de OBS. Acciones: escena siguiente/anterior, ir a una escena, mostrar/ocultar una fuente de la escena actual (ej. «Fondo negro»), silenciar un micro, subir/bajar su volumen (la velocidad son dB por clic) e iniciar/parar grabación o directo. La plantilla «OBS Studio» y la receta «Volumen del micro (OBS)» lo dejan listo con la entrada `Mic/Aux`; cambia el nombre si tu micro se llama distinto.

## 3. La pantalla

El selector de modo encabeza la pantalla y el Docker aparece debajo. Pulsa el lápiz de un control para editarlo: se abre un panel superpuesto con una cruz para cerrarlo en cualquiera de los tres modos. En Inteligente y Modos, las opciones de aplicación o modo siguen al Docker.

### Cabecera y acciones laterales del visor
- **Píldoras de estado:** ámbar = simulador; verde = teclado real conectado y estado del motor.
- **Enchufe:** busca el teclado de nuevo.
- **Columna derecha del visor (`✓` / `×`):** pegada a la derecha del dibujo del docker sin desplazar su centro. El botón **`✓`** escribe/aplica los cambios y se ilumina en **rojo completo** cuando hay cambios sin aplicar o el teclado no está preparado; debajo aparece **`×`** para descartar los cambios pendientes.
- **Minimizar / cerrar:** la ventana es propia (solo en el programa de escritorio).
- **Tamaño fijo (720 × 420):** no se redimensiona ni se maximiza. Los menús se abren como capa sobre el docker y caben dentro de la ventana.

### ① El teclado (centro)
- **Directo / Inteligente** está justo encima: es el modo de trabajo (ver sección 2b).
- En modo Inteligente, el botón de capas junto a los modos abre el panel **Atajos para:**, superpuesto sobre el docker, con un icono por cada app (su nombre aparece al pasar el ratón) y «Añadir app». A la derecha, la app que tienes en primer plano (ignora a RevienDocker: si vuelves a la ventana, sigue mostrando la última app real). Si esa app aún no tiene atajos, sale el botón **Crear atajos para <app>**: un clic y ya tiene su pestaña.
- Encima del teclado, una línea visual explica la regla de la pestaña elegida, por ejemplo `Shift + Botón → OBS Studio` («mantén Shift mientras pulsas, con esa app en primer plano») o `Botón → cualquier app` («pulsa el botón solo»). La tecla de activación (Shift, Ctrl o Alt; una sola, común a todo Inteligente) se elige con los tres iconos a la izquierda del docker: ↑ Shift, ^ Ctrl, ⌥ Alt. En las apps, sus ajustes (nombre, programas, quitar) están en «Atajos para».
- **KEY 1/2/3:** las tres teclas mecánicas. Muestran la acción asignada (ej. `Ctrl+Shift+F13`).
- **↺ / ↻:** giro de la rueda a izquierda / derecha.
- **Círculo central:** clic del pomo.
- **Clic directo en una pieza:** abre directamente la ventana de **Grabación** para asignarle una tecla, combinación o botón del ratón al vuelo.
- **Icono de lápiz (`✎`) debajo de cada pieza (Tecla 1, Tecla 2, Tecla 3 y Rueda):** único botón que abre o cierra debajo el panel **② Elige qué hace** para editar esa pieza en detalle. Si ningún lápiz está activo, el panel ② permanece oculto.
- **Menús plegados por defecto:** todos los desplegables arrancan cerrados y se cierran al cambiar entre **Directo**, **Inteligente** y **Modos** (o al cambiar de app o de hueco de modo), abriéndose solo lo que selecciones.
- **Plantillas:** elige un chip (icono y nombre) para revisar los seis controles antes de confirmar. Hay opciones para música, WoW Forever, navegación, reuniones, edición, trabajo diario y OBS. Las teclas fantasma F13–F18 sirven para asignar acciones en otros programas; no hacen nada por sí solas.
- **Diagnóstico:** contiene el registro técnico USB, separado de las plantillas.
- **Luz del teclado** (botón de bombilla y paleta junto al selector de modo): interruptor y tres modos: **Apagada**; **Al pulsar** (cada pulsación enciende la tecla con el siguiente color de la serie azul, rojo, verde…); **Ciclo** (una pulsación lanza un ciclo de colores por las teclas 1, 2 y 3). Se aplica al instante y queda en el teclado, sin pulsar «Aplicar cambios». El color no se puede elegir: lo decide cada modo.

### ② Elige qué hace (icono de lápiz)
Se abre únicamente al pulsar el lápiz (`✎`) debajo de una tecla o de la rueda. Cuando editas la rueda, arriba aparece un selector compacto (`↺ Izq. | ● Pulsar | ↻ Der.`) para inspeccionar, probar o borrar cada parte.

- **Asignado ahora:** la acción actual en chips (`Ctrl + Shift + Z`), con su tipo y el contador `n / 3 teclas`. Si lleva velocidad, aparece un selector.
- **Grabación directa (pulsando la pieza en el visor ①):** abre la ventana de grabación. Pulsa la combinación, haz clic con cualquier botón del ratón (izquierdo, derecho, central, atrás, adelante) o mueve la rueda. Se guarda sola al soltar. Se puede combinar con Ctrl/Shift/Alt/Win (ej. Ctrl + clic derecho, Ctrl + rueda).
  - En el programa de escritorio la captura de teclado la hace el motor nativo (hook de Windows): Alt+Tab, Win y similares se graban sin que el PC los ejecute. Tiene un tiempo máximo de 20 s por seguridad. Para salir sin guardar: «Cancelar».
  - En un navegador (desarrollo) se usa pantalla completa + bloqueo de teclado como alternativa menos fiable.
  - **Ctrl+Alt+Supr es imposible de capturar** (lo trata el propio Windows). Para eso y para los demás atajos del sistema están los «Atajos del sistema».
- **Límite:** 1 tecla, o combinación de 2 o 3 en total, contando los modificadores. Ctrl+C = 2, Ctrl+Shift+F13 = 3. Una combinación es modificadores + una sola tecla normal (o un botón/rueda del ratón).
- **Atajos del sistema:** Alt+Tab, Win+Tab, Alt+F4, Win+D, Win+L, Win+E, Win+V, Win+Shift+S, Ctrl+Alt+Supr, Ctrl+Shift+Esc, Win+., Alt+Esc. Un clic y se asignan sin grabar.
- **Acciones de OBS:** escenas, fuentes y micrófono en el editor de la app OBS; la conexión WebSocket está en sus ajustes.
- **Probar / Borrar:** prueba la acción tras 3 segundos o deja el botón sin asignar.
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

- **Paso de volumen:** elige ±1, ±2, ±3 o ±5 puntos porcentuales por muesca; se aplica a ambos sentidos. RevienDocker debe estar abierto o en la bandeja también en Directo. La primera vez hay que pulsar «Aplicar cambios» para preparar la rueda. En scroll y zoom, el selector sigue indicando un multiplicador de rueda.
- **⇄ Invertir sentido:** intercambia giro izquierdo y derecho.
- Después de aplicar una receta puedes retocar cualquier parte con grabar o a mano.

## 4. Cómo funciona por dentro

1. La interfaz guarda todo (modo, capas, acciones) en el navegador y, con el servidor activo, en `studio.json`. Se recupera al reabrir.
2. Al flashear genera mensajes de 64 bytes (el primero es el Report ID `03`): por cada botón **inicio `FE` → datos → cierre `AA AA`**, y al final 3 mensajes de luz.
3. Los envía por uno de estos caminos, en este orden:
   1. WebHID, si pulsaste «Conectar».
   2. El backend Python (`POST /api/flash`), que usa `hidapi` si hay teclado y simula si no.
   3. Simulación dentro del navegador, si abriste el HTML sin servidor.
4. Formatos (el de ch57x-keyboard-tool para el CH57x 0x8890): tecla = un mensaje vacío `03 <slot> 11 01` + `03 <slot> 11 01 01 <mod> <código>`; multimedia `03 <slot> 12 <lo> <hi>`; ratón `03 <slot> 13 <botones> 00 00 <rueda con signo> <mod>`; luz `03 A1 01`, `03 B0 18 <modo>`, `03 AA A1`. El volumen ajustable usa teclas fantasma para que el motor cambie el nivel en Windows.

Slots: KEY_1 `01`, KEY_2 `02`, KEY_3 `03`, rueda izq. `0D`, clic `0E`, rueda der. `0F`.

## 5. Flujo recomendado

1. Elige un preset o ajusta botón a botón.
2. Revisa las tramas en la consola.
3. Con el teclado: pulsa el enchufe para detectarlo y «Aplicar cambios».
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
| 2026-11-02 | **Ventana fija y menús compactos.** La ventana pasa a 720 × 420 sin redimensionar ni maximizar, con los espacios verticales recortados y el carril y la botonera a la misma distancia del docker. La tecla de activación de Inteligente (una sola) pasa a los tres iconos del carril izquierdo. «Añadir una app» y las plantillas de Modos usan chips con icono y nombre, como «Atajos para»; las plantillas viven solo en el menú de cada hueco. ✓ verde y × rojo, selección con borde blanco y halo. Estilo oficial y decisiones de producto en `PRODUCT.md` (sustituye a `DISEÑO.md`). |
| 2026-11-02 | **Modos más claros.** Misma estructura en Directo, Inteligente y Modos (barra superior, iconos + docker + iconos, mensaje centrado). «Nuevo modo» sustituye al botón «Modo en blanco» y es una plantilla más, con nombre e icono a elegir; el icono de cualquier modo se cambia desde su menú. Mini docker en la vista previa de las plantillas. El aviso nativo del modo activo pasa a abajo a la derecha, sobre la bandeja. |
| 2026-11-02 | **Menús superpuestos sobre el docker.** Los paneles de Directo (perfiles), Inteligente (Atajos para) y Modos (plantillas y menú de cada hueco) se abren como capa encima del docker, sin empujarlo. |
| 2026-11-02 | **Modos con Ctrl+Shift** (antes Alt+Shift). Carril de iconos a la izquierda del docker, uno por hueco: su menú cambia el nombre, elige plantilla o vacía el hueco (la plantilla no se borra). El icono de ajustes de la cabecera sigue abriendo las plantillas. «Atajos para» muestra un icono por app en lugar de su nombre. Ancho mínimo 712 × 560: el docker nunca se apila; `✓` y `×` siempre a la derecha.
| 2026-11-01 | Unificación de **Directo / Inteligente / Modos** (3 huecos con plantillas y cambio rápido con `Alt+Shift+1/2/3` + overlay compacto). Limpieza visual del visor: sin barra informativa bajo las pestañas, botón de aplicar/descartar (`✓` / `×`) a la derecha del visor con aviso en rojo completo, clic directo en cada pieza para grabar al vuelo, icono de lápiz (`✎`) bajo cada pieza para abrir el menú 2, eliminación de «Elegir a mano» y menús plegados por defecto. |
| 2026-11-01 | Control de instancia única por mutex nativo y HTTP: evita iconos duplicados en la bandeja al abrir y minimizar. Nueva 3ª opción «Modos» (placeholder con icono Lucide Shapes) en el selector de la cabecera. |
| 2026-11-01 | Rediseño de uso: una columna central con el selector de modo sobre el teclado, secciones plegables de una en una con más aire y subtítulos, pestañas «Atajos para» por app con detección de la app real y atajo «Crear atajos para…», regla visual `Shift + Botón → App`. |
| 2026-11-01 | «Flashear» pasa a «Aplicar cambios» con «Descartar», aviso de teclado desconocido y luz con los 3 modos reales (comprobados en el teclado y en el programa del fabricante). |
| 2026-11-01 | Escritura USB corregida (formato real del CH57x 0x8890, errores de escritura visibles) y nueva sección «Luz del teclado» con envío en vivo. |
| 2026-10-31 | v0.02: icono nuevo (`assets/ICON.jpg` → `icon.png/.ico`), título metálico en Doris PP, interfaz en Expressway, esquinas suaves (nunca cuadradas) y documento de diseño (hoy integrado en `PRODUCT.md`). |
| 2026-10-31 | v0.01: ventana redimensionable por bordes y esquinas (zonas propias, la ventana sin marco no tenía borde nativo), diseño que se adapta de 820 a 1400 px (flujo del modo Inteligente sin saltos de fila, dos columnas pasan a una en anchuras medianas), botones de ventana visibles también al arrancar en modo Directo, lista blanca de acciones en `/api/window`. |
| 2026-10-31 | Renombrado a **RevienDocker**: icono nuevo (R · v · D), ventana propia sin marco y compacta, iconos Lucide, interfaz reducida con flujo visual, grabación nativa de teclado, aviso de «sin flashear». |
| 2026-10-31 | Aplicación de escritorio: `RevienDocker.exe` con ventana, bandeja, instancia única y USB por hidapi. |
| 2026-10-31 | Rediseño completo (studio.css / studio.js), modo Inteligente con capas por app, tecla de activación, motor Windows, OBS WebSocket nativo, persistencia, botón Probar. |
| 2026-10-31 | Grabación real con paso intermedio, captura total en Chrome/Edge, atajos listos, ratón completo, recetas de rueda y velocidad. |
| 2026-10-31 | Editor de botón con captura de teclado (1 a 3 teclas), pestañas y catálogo completo de teclas. |
| 2026-10-31 | Proyecto recuperado de Drive; modo simulador, LED, preset Dev, WebHID, pruebas. |


## Perfiles de Directo

En Directo, el botón «+» junto a los modos abre los perfiles. Confirma primero las asignaciones con ✓ y guárdalas con un nombre de hasta 12 caracteres. Selecciona un perfil para cargar sus acciones; usa la papelera para eliminarlo. Los cambios cargados se confirman con ✓.

## Modos de trabajo

Con **Ctrl+Shift+1/2/3** cambias de hueco (repetirlo vuelve a Directo).

- **Carril de iconos** a la izquierda del docker: un icono por hueco. Pulsa uno para seleccionarlo y abrir su menú, superpuesto sobre el docker: nombre (se guarda al salir del campo), icono (pulsa el icono de la cabecera del menú y elige otro), **Plantilla** y **Vaciar**. La cabecera recuerda su atajo (Ctrl+Shift+1/2/3).
- **Vaciar** deja el hueco libre. La plantilla no se borra: sigue disponible entre las plantillas.
- Un hueco vacío (**«+»**) abre directamente las **plantillas**; en un hueco con modo, **Plantilla** las abre dentro del mismo menú (con una flecha para volver). Es la única puerta a las plantillas.
- Las plantillas son chips con icono y nombre. Al elegir uno, debajo aparece la vista previa (mini docker y descripción) y «Usar en este modo» la aplica y cierra el menú.
- El botón de la izquierda del selector (▶) **activa el modo seleccionado ahora** (o vuelve a Directo si ya está activo), sin usar el teclado.
- **Nuevo modo** es una plantilla más (el último chip): pide un nombre y un icono (16 a elegir en una fila) y «Crear modo» crea el modo vacío y cierra el menú. Lo que no definas en él hace lo de Directo.
- Al activar un modo (con Ctrl+Shift+1/2/3 o desde la app) o volver a Directo, sale un aviso nativo muy breve (icono y nombre) abajo a la derecha, justo encima de la barra de tareas y de la bandeja, sin quitar el foco a lo que estés haciendo. Así sabes qué modo está activo aunque la app esté minimizada.
- En **Directo** e **Inteligente** el carril de la izquierda muestra tres huecos reservados (discontinuos y desactivados): la estructura de pantalla es la misma en los tres modos.
