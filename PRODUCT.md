# RevienDocker · Producto

<!-- impeccable:product-schema 1 -->

> Fuente única de producto y estilo. Sustituye a `DISEÑO.md`. Cualquier cambio visual o de comportamiento se decide aquí primero.
> Origen: sesión de definición con Revien (2026-11-02) sobre capturas anotadas. Las decisiones marcadas «Decisión» las tomó Revien; las marcadas «Criterio» son mías y están para que las corrija.

## Platform

web

(Aplicación de escritorio de Windows: interfaz web ligera en una ventana `pywebview` sin marco, motor en Python.)

## Users

Revien y personas que usan un macropad CH57x de 3 teclas y 1 rueda junto al PC. Lo usan en mitad de otra tarea (streaming, música, reuniones, juego, trabajo), casi siempre con la app **minimizada o en la bandeja**. Abren la ventana solo para configurar; el resto del tiempo el docker trabaja solo.

## Product Purpose

Configurar el macropad desde el PC y hacer que cada botón haga lo útil en cada momento, sin tocar firmware ni terminal. Éxito: el usuario sabe qué hace cada botón, cambia de modo sin mirar la pantalla y configura algo nuevo en pocos clics.

## Positioning

Un docker físico con tres formas de uso sobre el mismo aparato y la misma pantalla: **Directo** (siempre igual), **Inteligente** (cambia según la app en primer plano) y **Modos** (tres configuraciones que se cambian con Ctrl+Shift+1/2/3). Misma estructura visual en las tres.

## Operating Context

- El motor (`src/studio_engine.py`, gancho de teclado de Windows, teclas fantasma F13–F18) debe estar en marcha; cerrar la ventana la oculta en la bandeja y minimizar también: la app solo existe en la bandeja, sin botón en la barra de tareas ni en Alt+Tab.
- El usuario sabe qué modo está activo por un **aviso nativo breve** abajo a la derecha, sobre la bandeja, no por la app.
- Configuración en `%APPDATA%\RevienDocker\studio.json`. Solo escucha en `127.0.0.1`.
- Se compila a `dist\RevienDocker.exe` y se abre desde el acceso directo del escritorio. Recompilar tras cada tanda.

## Capabilities and Constraints

### Estructura canónica (Decisión)
Idéntica en Directo, Inteligente y Modos; no se inventan variantes por modo:
- **Lateral izquierdo (0.0.8):** el logotipo definitivo a toda la altura (título «REVIENDOCKER» en vector, girado, y el dibujo del interruptor). Sustituye a la barra superior, que **ya no existe**. Es también zona de arrastre de la ventana.
- **Franja inferior (0.0.8):** minimizar, cerrar y la rueda dentada de **ajustes**, discretos, abajo a la derecha. **Toda zona no interactiva** de la ventana (lateral, fondos, textos, huecos de la franja) arrastra la ventana; botones, campos y teclas no.
2. **Selector:** botón contextual + selector Directo / Inteligente / Modos + luz (solo la bombilla, mismo tamaño y aspecto que el botón de la izquierda, para que la fila quede simétrica).
3. **Fila del docker:** tres iconos a la izquierda + docker (3 teclas y rueda, sin lápices bajo las piezas) + ✓ y × a la derecha. El carril izquierdo y la botonera derecha están **a la misma distancia** del docker.
4. **Mensaje informativo centrado** debajo.

### Ventana (Decisión)
- **Tamaño fijo, 720 × 420.** No se redimensiona, no se maximiza, no se expande ni se colapsa. Sin botón de maximizar; el doble clic en la barra y el arrastre de bordes no hacen nada. Minimizar y cerrar se mantienen.
- **Posición inicial:** esquina inferior derecha del área útil (sobre la barra de tareas, 12 px de margen). Después se puede arrastrar; se recoloca solo al abrir. La ventana nace fuera de pantalla y solo se muestra ya colocada (sin parpadeo en otra esquina).
- Sin margen muerto: el contenido llena el marco. Espacios verticales compactos entre barra, selector, docker y mensaje.
- Los menús son **capas superpuestas** sobre el docker, nunca debajo ni en flujo; deben caber en la ventana y, si algo no cabe, desplazan por dentro.
- Los menús terminan donde acaba el docker y no tapan el mensaje de abajo.

### Ajustes (Decisión, 0.0.8)
La rueda dentada, a la derecha de la ×, despliega **hacia arriba y en vertical** tres iconos: teclado (estado), rayo (motor, estado) y enchufe (buscar el teclado). Solo iconos, sin texto (nombre en tooltip y para lectores de pantalla). Los puntos de estado ámbar/verde/rojo viven dentro del menú; la rueda lleva su propio punto **solo si algo no va bien** (ámbar: sin teclado o motor arrancando; rojo: motor caído). Se cierra al pulsar fuera, con Esc o tras buscar el teclado; seleccionada = borde blanco con halo y giro de 60°.

### Directo (Decisión: de momento no se toca)
Perfiles guardables desde «+» junto a Directo, cada uno con nombre e icono. Los tres huecos del carril izquierdo son accesos a perfiles (0.1.4): vacío = «+» discontinuo que abre la lista; con perfil = su icono, un clic lo usa y el que coincide con las teclas se marca en blanco. Un perfil ocupa un solo hueco; el nuevo va al primero libre.

### Inteligente (Decisión)
- Cada botón cambia según la app en primer plano. El icono de capas abre «Atajos para» (apps y sus ajustes) como capa superpuesta.
- **Tecla de activación:** **una sola** (Shift, Ctrl o Alt; excluyente, porque con dos se podría activar un modo sin querer). Es **global** a todo Inteligente (`S.trigger`). Sale del menú y pasa a los **tres botones del carril izquierdo**, rotulados con texto corto (Shift / Ctrl / Alt) porque los iconos no se entendían; el texto «Tecla de activación» desaparece y cada botón añade su explicación al pasar el ratón o al enfocar.
- **«Añadir app»** y «Atajos para» comparten formato de chips con **icono + nombre corto**, sin párrafos. Las apps abiertas entran en una cuadrícula compacta; el campo «O escribe el programa» y «Cerrar» siguen a la vista.

### Modos (Decisión)
- Tres huecos, cada uno con nombre e icono elegidos por el usuario (17 iconos y, al final de la fila, un «+» discreto de borde discontinuo que despliega 34 de apps y marcas; si el icono actual es de una app, la fila sale abierta; todo cabe en la ventana de 720 × 420). Ctrl+Shift+1/2/3 activa; repetir vuelve a Directo.
- **Confirmación física (0.1.0):** la pulsación de cambio de modo enciende brevemente la tecla del macropad (unos 450 ms), incluso con luz Apagada; después se restaura la preferencia. Es un aviso de entrada/salida, no un indicador permanente. En Al pulsar se conserva el efecto nativo. Cambiar el hueco desde la interfaz no genera un aviso físico: el firmware recuerda la última tecla del aparato, no una selección por software.
- **Una sola puerta a plantillas y Mis modos:** los tres iconos del carril seleccionan el hueco; el botón «+» superior abre su menú (nombre, icono, Guardar en Mis modos, Quitar del hueco), o las plantillas y Mis modos si está libre.
- **Plantillas como chips** con icono y nombre; la descripción va en una línea al elegir, no en cada tarjeta.
- **Mis modos (0.1.1, Decisión):** hasta **3 modos propios** guardados, en chips bajo las plantillas. «Nuevo modo» (nombre + icono) crea y guarda; hereda de Directo lo que no defina. Usar una plantilla o un modo guardado **copia** al hueco: editar el hueco nunca cambia la plantilla ni lo guardado; «Guardar cambios» actualiza lo guardado (el hueco recuerda su origen con `from`). Se borra desde un hueco libre. Con 3 guardados, «Nuevo modo» queda desactivado. Quitar del hueco solo pide confirmación si se pierde algo.
- **Vista previa compacta** (mini docker + «Usar en este hueco»), sin empujar la rejilla. El mini docker aparece solo aquí.
- El editor de opciones se abre desde la grabación y conserva recetas de rueda y OBS. Los atajos se graban con las teclas, sin catálogo predefinido.

### Aviso nativo de modo
`src/volume_overlay.py`: 280 × 56 px, siempre visible, sin foco, fuera de la barra de tareas, esquina inferior derecha del área útil con 16 px de margen, 1,8 s. Icono y nombre. No es una notificación del Centro de actividades.

### Técnicas
Estructura: `src/` (Python), `web/` (interfaz y assets), `docs/`, `tools/`, `tests/`. Interfaz estática, sin build ni dependencias de front. Ventana de escritorio fija de 720 × 420 (`WIN_W, WIN_H` en `src/studio_app.py`). Iconos Lucide generados (`tools/build_icons.py`, 68 iconos) más 34 propios de apps y suites (`tools/custom_icons.py`: dibujados a mano, sin copiar de ningún paquete). No se ofrecen para elegir: salen solos al detectar el programa (`APP_ICONS` en `web/studio.js`, gana la primera coincidencia). Estado `S` en `localStorage` `botonera.studio.v2` y `studio.json`. Los originales y datos de cada persona no salen del PC.

## Brand Commitments

- **Nombre:** RevienDocker. Wordmark «REVIENDOCKER» en vector (`assets/wordmark.svg`), Doris PP, mayúsculas con R y D más altas, degradado metálico solo de opacidades de blanco. Va girado en el lateral izquierdo, junto al dibujo del interruptor (`assets/logo-switch.jpg`, recorte de `docs/LOGO_DEFINITIVO_LATERAL.jpg`). El texto de esa imagen sale mal escrito («Revbcker»), por eso el título se pone siempre con el vector.
- **Icono:** `assets/Icon_definitivo.jpg` → `studio_icon.py` genera `icon.ico`, `icon.png` y `brand-icon.png`. Dibujo sobre negro, sin marco blanco.
- **Voz:** español de España, tuteo, frases cortas, sin tecnicismos de más.
- **Concepto:** macropad como **mecanismo de relojería**: teclas de cera negra, base translúcida. Blanco y negro limpio sobre negro profundo.

## Sistema visual (oficial)

### Paleta
Tokens en `:root` de `studio.css`. **Sin color de acento**: la identidad es blanco sobre negro; el color solo informa de un estado.

| Token | Valor | Uso |
|---|---|---|
| `--bg` | `#08090c` | Fondo de ventana |
| `--panel` / `--panel-2` / `--panel-3` | `#0f1218` / `#151a23` / `#1c2330` | Paneles, controles, hover y seleccionado |
| `--line` / `--line-2` | `#222a38` / `#323d52` | Bordes finos / bordes activos |
| `--text` / `--muted` | `#eef1f6` / `#8791a3` | Texto principal / secundario |
| `--accent` | `#ffffff` | Acción primaria y selección |
| `--green` | `#4ade80` | **✓ aplicar**, conectado, correcto |
| `--red` | `#f87171` | **× descartar/cerrar-sin-guardar**, borrar, error |
| `--amber` | `#fbbf24` | Atención, cambios sin aplicar, buscando |

### Lenguaje de estados (Criterio, a validar)
Un solo vocabulario en toda la app, para que el usuario lea el estado sin pensar:

| Estado | Señal |
|---|---|
| Reposo | Borde `--line`, texto `--muted` |
| Hover (solo puntero fino) | Borde `--line-2`, fondo `--panel-3` |
| Hover en teclas, rueda y giros | Aro gris claro (`rgba(255,255,255,0.4)`, 1 px) sobre la tecla, la rueda o la pastilla; el seleccionado mantiene el blanco |
| Pulsado | `scale(0.97)`, 160 ms |
| **Seleccionado / activo** | Borde blanco 1 px + fondo `--panel-3` + texto blanco + halo suave `0 0 0 3px rgba(255,255,255,.08)` |
| Foco de teclado | Anillo blanco 2 px, separado 2 px |
| **✓ Aplicar** | Reposo: tick verde con borde verde tenue. **Con cambios pendientes: verde sólido** (`--green`, texto oscuro) con halo verde |
| **× Cancelar** | Solo aparece con cambios sin aplicar: tick y borde rojo tenue; en hover, fondo rojo tenue. Descarta |
| Peligro (Quitar del hueco, borrar) | Texto `--red`, borde rojo tenue en hover |
| Desactivado / marcador | Borde discontinuo, opacidad 0,5, sin hover |

El rojo ya no se usa para el ✓ pendiente: el rojo significa siempre «quitar».

### Tipografía
Doris PP solo en el wordmark (vector). Expressway para toda la interfaz (cae a Inter / Segoe UI). Cascadia Code (respaldo JetBrains Mono / Consolas) para teclas y códigos. Las acciones del docker usan cursiva de peso 600 y gris claro suave en las tres vistas; la herencia se distingue con subrayado punteado, sin reducir la opacidad del texto. Los menús conservan Expressway con blanco suave y peso 600. Números que cambian: `tabular-nums`. No hay fuentes embebidas en el exe.

### Esquinas
Ninguna esquina a 90º ni radio 0. Controles, paneles, teclas y píldoras 4 px; contenedores `--r` 6 px; botones de ventana 3 px; perilla y puntos 50 %.

### Superficies y capas
Menús = capa superpuesta sobre el docker (`.deck-drawer`, fija, anclada arriba y centrada sobre el área de contenido, a la derecha del lateral, z-index 40) con cierre en su cabecera; las plantillas y el editor de tecla se anclan más arriba para caber enteros. Un menú abierto a la vez. Sin sombras de neón ni degradados de color.

### Movimiento
Curvas `--ease-out: cubic-bezier(0.23,1,0.32,1)`, `--ease-in-out: cubic-bezier(0.77,0,0.175,1)`. Solo `transform` y `opacity` (más color y borde). Feedback de botón 100–160 ms; capas y menús 160–220 ms al entrar y más rápido al salir; las capas nacen desde `scale(0.97)` + `opacity 0`, nunca desde 0. Nada se anima con atajos de teclado. Hover solo bajo `@media (hover: hover) and (pointer: fine)`. `prefers-reduced-motion`: se conservan opacidad y color, desaparece el movimiento.

## Evidence on Hand

- Capturas anotadas por Revien (2026-11-02): ventana a tamaño fijo y huecos a recortar, Añadir app a chips, tecla de activación al carril.
- `docs/GUIA_USUARIO.md` (uso), `CHANGELOG.md` (historial), `README.md` (instalación), 30 pruebas automáticas en `tests/`.
- Sin pruebas con usuarios ajenos ni métricas de uso: no se inventan.

## Product Principles

1. **La app es un mando, no un lugar donde estar.** Lo importante pasa con la ventana minimizada; la ventana solo configura.
2. **Una estructura, tres modos.** Lo que se aprende en uno sirve en los otros dos.
3. **Compacto antes que completo.** Ventana fija, chips en vez de párrafos, capas en vez de páginas.
4. **El estado se ve, no se lee.** Seleccionado, pendiente, correcto y peligro tienen siempre la misma señal.
5. **Nada se confirma a ciegas.** Cambiar de modo, aplicar o vaciar dan respuesta inmediata y visible.

## Accessibility & Inclusion

Foco visible en todo. Etiquetas en español (`aria-label`) en iconos sin texto; los marcadores desactivados se ocultan a lectores de pantalla. Contraste mínimo AA sobre `--bg`. Objetivos táctiles/clic ≥ 30 px. Movimiento reducido respetado.

## Puntos abiertos

1. Icono negro: se funde con una barra de tareas oscura. ¿Se deja?
2. Licencia de Doris PP para el wordmark vectorial y fuentes sin embeber (Expressway solo Rg; 600/700 sintetizados).
3. Directo e Inteligente tendrán iconos propios en el carril izquierdo en el futuro; hoy son marcadores (Directo) y tecla de activación (Inteligente).
4. Si «Quitar del hueco» sobre el hueco activo debe devolver el motor a Directo (hoy el motor puede quedar apuntando a un hueco vacío).

### Giros de rueda (0.0.11)
Dos pastillas independientes de 56 × 30 px separadas por un icono de rueda. Cada pastilla graba su propio giro. Texto en una línea con elipsis y asignación completa en tooltip y nombre accesible. Se retiran los lápices y la lista de atajos predefinidos; las opciones de la grabación conservan velocidad, recetas y OBS.
