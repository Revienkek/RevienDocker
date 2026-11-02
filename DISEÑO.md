# RevienDocker · Diseño artístico

> Documento para revisión. Describe la dirección visual actual de la app y del icono; los puntos abiertos están al final.

![Icono de RevienDocker](assets/icon.png)

## Concepto

Un macropad CH57x visto como **mecanismo de relojería**: teclas de cera negra, base translúcida con engranajes y tornillos. El lenguaje es **blanco y negro limpio sobre negro profundo**: sin color de acento, sin degradados de color, sin sombras de neón. El color solo aparece como estado (verde, ámbar, rojo) en píldoras y puntos.

## Icono

- Fuente: `assets/Icon_definitivo.jpg` (ilustración definitiva, fondo negro).
- `studio_icon.py` elimina el fondo negro exterior, conserva las zonas negras del dispositivo y su halo, y ajusta la ilustración al espacio disponible.
- Salidas independientes: `assets/icon.ico` (16 a 256 px) para Windows, `assets/icon.png` para la bandeja y `assets/brand-icon.png` para la cabecera. Se regeneran con `python studio_icon.py`.
- `assets/icon.svg` ya no se usa; se puede borrar cuando lo confirmes.

## Logotipo

- `assets/wordmark.svg`: «REVIENDOCKER» en trazos vectoriales, con la R inicial y la D de Docker más altas. No depende de la fuente instalada.
- La cabecera centra el wordmark sin icono lateral.

## Paleta

Todo son tokens en `:root` de `studio.css`:

| Token | Valor | Uso |
|---|---|---|
| `--bg` | `#08090c` | Fondo de la ventana |
| `--panel` | `#0f1218` | Paneles y barra de título |
| `--panel-2` / `--panel-3` | `#151a23` / `#1c2330` | Controles y hover |
| `--line` / `--line-2` | `#222a38` / `#323d52` | Bordes finos |
| `--text` / `--muted` | `#eef1f6` / `#8791a3` | Texto principal y secundario |
| `--accent` | `#ffffff` | Acciones primarias (blanco sobre negro) |
| `--green` / `--amber` / `--red` | `#4ade80` / `#fbbf24` / `#f87171` | Estados y botón de aplicar con cambios pendientes (`#btnFlashAll.alert`) |

## Tipografía

Dos fuentes **instaladas en el sistema**:

- **Doris PP** (`--font-title`): «REVIENDOCKER» en mayúsculas, interletrado 0.06 em. En la app va como vector (`assets/wordmark.svg`), así que no depende de la fuente instalada.
- **Expressway** (`--font`, cae a Inter y Segoe UI): toda la interfaz.

Las fuentes no están embebidas en el ejecutable. En un PC sin ellas la app usa el sistema de respaldo.

## Título metálico

Degradado de **opacidades** en blanco (sin color), dentro del SVG:

- Degradado lineal con bandas de blanco pleno y blanco al 28–62 % para el efecto de metal pulido.
- Filete de 0,02 em al 30 % de blanco, que da el borde fino. Sin sombras ni desenfoques: el brillo es el propio degradado.

## Esquinas

Regla: **ninguna esquina llega a 90º ni queda pura (radio 0)**.

- Controles, paneles, teclas y píldoras: **4 px**; contenedores grandes (`--r`): **6 px**.
- Botones de ventana: **3 px** (antes 0).
- Perilla y puntos de estado: círculos (`50%`), que no tienen esquinas.
- Indicador de la perilla: 2 px, es una barra fina, no una caja.

## Visor del dispositivo y edición

- Norma: el docker siempre se ve completo y en una sola fila: carril de modos (`.mode-rail`, a la izquierda) | visor `.acrylic-case` | botonera `.chassis-side` (`✓` y `×`, a la derecha). Nunca se apilan. El ancho mínimo de la ventana (712 px, `MIN_W` en `studio_app.py`) es esa fila entera.
- El carril existe también fuera de Modos, vacío y oculto (`visibility`), para que el visor no salte al cambiar de pestaña.
- Cuando hay cambios pendientes o el teclado requiere preparación, el botón `✓` cambia a fondo rojo completo (`--red`) en lugar de usar un punto flotante.
- Debajo de cada pieza del visor (Tecla 1, Tecla 2, Tecla 3 y Rueda) se sitúa un botón compacto de lápiz (`.edit-pen`, 30 × 26 px): pulsar la pieza lanza la grabación directa y pulsar su lápiz abre o cierra el panel ② de edición en detalle.
- Todos los desplegables (`.fold`) permanecen cerrados por defecto y se pliegan al cambiar entre Directo, Inteligente y Modos.

## Movimiento

- Curva `cubic-bezier(0.23, 1, 0.32, 1)`.
- Solo se animan `transform` y `opacity` (color y borde en hover).
- Los estados de hover van dentro de `@media (hover: hover) and (pointer: fine)`.

## Para revisar

1. **Icono negro**: el icono es el dibujo sobre negro, sin marco blanco. En una barra de tareas clara se distingue bien; en una oscura se funde con el fondo. ¿Lo dejamos así?
2. **Fuentes**: el wordmark ya es vector (trazos de Doris PP), así que la licencia de Doris PP hay que confirmarla para ese uso. Expressway sigue sin embeberse en el ejecutable.
3. **Negrita de Expressway**: solo tengo la variante Rg; los pesos 600 y 700 se sintetizan y pueden verse borrosos.
4. **Radios**: 4 px en controles y 6 px en contenedores. ¿Te parece bien esa proporción?
5. **Título en mayúsculas** con el degradado: ¿lo prefieres en tipo mixto?

## Perfiles de Directo

El selector de perfiles se abre desde el icono «+» junto a Directo. Su panel es una capa superpuesta sobre el docker. El panel compacto usa iconos para guardar y eliminar, y limita los nombres a 12 caracteres.

## Jerarquía y edición

El Docker precede a las opciones de app o modo. En los tres modos, el lápiz abre el editor superpuesto y conserva la altura de la vista. La cruz comparte la fila superior con la asignación. La conexión WebSocket aparece dentro de los ajustes de la app OBS.

En Inteligente, el icono de capas abre las apps y sus ajustes en una capa superpuesta sobre el docker; la cruz comparte la cabecera con «Atajos para».

En Modos, los iconos del carril seleccionan cada hueco y abren su menú; el icono de ajustes abre el panel de plantillas. Ambos son capas superpuestas sobre el docker, y tienen cierre en su cabecera. Los números de hueco son discretos (opacidad baja) para no competir con el dibujo.
