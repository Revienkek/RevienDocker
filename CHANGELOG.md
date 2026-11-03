# Historial de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). Versiones `0.x.y`: una por tanda de trabajo.
La versión actual está en `src/version.py` y en el nombre de la etiqueta de GitHub (`v0.x.y`). Producto y estilo: [PRODUCT.md](PRODUCT.md).

## Pendiente de publicación

### Corregido
- Cambiar la velocidad o las asignaciones y pulsar Aplicar ya no vuelve a escribir el macropad cuando ya está preparado. Se conserva completa la firma de preparación para reconocerlo tras reiniciar.

## [0.1.6] · 2026-11-02 · Aviso de cambios y hover en los modos

### Cambiado
- Con la × roja a la vista, el mensaje de bajo el docker pasa a «Tienes cambios sin guardar», tenue y con borde rojo.
- Directo, Inteligente y Modos se iluminan sutilmente al pasar el ratón (el activo conserva su borde blanco).

## [0.1.5] · 2026-11-02 · Clic fiable en la bandeja

### Corregido
- Al pulsar el icono de la bandeja la ventana ya no aparecía detrás de otras ni había que hacer dos o tres clics: se sube al frente aunque Windows no le dé el foco, y si ya está visible pero tapada por otra ventana, el clic la sube en vez de ocultarla. Solo se oculta si está a la vista.
- Un aviso de «minimizada» que llegaba justo al mostrarla la volvía a ocultar al instante; ahora se ignora.

## [0.1.4] · 2026-11-02 · Perfiles en el lateral y solo en la bandeja

### Añadido
- Los tres huecos de la izquierda en Directo son accesos a tres perfiles: un clic usa el perfil al momento, se marca el activo y un hueco libre abre la lista para elegir. Cada perfil tiene icono propio (selector como en Mis modos) y tres marcas 1/2/3 para ponerlo o quitarlo de un hueco. Un perfil nuevo ocupa el primer hueco libre.

### Cambiado
- La ventana pasa de 720 × 420 a 720 × 348: se quita la franja vacía bajo el mensaje. El lateral se reajusta: el título gana tamaño en la R y la D y el resto va en versalitas más pequeñas, y el dibujo del interruptor se reduce un 16 %.
- Clic derecho en una zona de arrastre devuelve la ventana a la esquina inferior derecha, sobre la barra de tareas.
- Minimizar manda la ventana a la bandeja, siempre. La app ya no tiene botón en la barra de tareas ni en Alt+Tab: solo se ve en la bandeja del sistema.
- Los perfiles guardados antes reciben identificador e icono sin perder nada.

### Corregido
- Al abrir, la ventana ya no parpadea en otra esquina antes de colocarse: nace fuera de pantalla y solo se muestra ya colocada, sobre la barra de tareas. Arrancar en la bandeja (`--minimized`) deja la ventana oculta.

## [0.1.3] · 2026-11-02 · Hover en teclas y rueda

### Corregido
- Las tres teclas, la pulsación de la rueda y los dos giros se iluminan al pasar el ratón con un aro gris claro, como el resto de controles. El elemento seleccionado conserva su borde blanco.

## [0.1.2] · 2026-11-02 · Iconos de apps

### Añadido
- 34 iconos propios de aplicaciones y suites (WoW, Spotify, OBS, Adobe, Google, Microsoft 365, Discord, Steam…), dibujados a mano con la rejilla y el trazo de Lucide. Salen solos al detectar el programa en «Añadir app» y en Inteligente.
- El selector de iconos de Mis modos termina en un «+» discreto que despliega esos iconos, y un icono más en la fila principal («Objetivo»). Sin salirse de la ventana de 720 × 420.

### Cambiado
- «WoW Forever» pasa a llamarse «WoW» en las plantillas. Spotify, WoW y OBS usan su icono propio.
- La vista previa de una plantilla se desplaza a la vista dentro del menú.
- El aviso nativo de modo usa el glifo de Windows más parecido para cada icono de marca.

## [0.1.1] · 2026-11-02 · Mis modos

### Añadido
- **Mis modos:** hasta tres modos propios guardados, junto a las plantillas. Se crean con «Nuevo modo» o con «Guardar en Mis modos» desde un hueco, se actualizan con «Guardar cambios» y se borran desde un hueco libre.
- Usar una plantilla o un modo guardado pone una copia en el hueco: editarla no cambia la plantilla base ni lo guardado hasta que lo guardes.

### Cambiado
- El menú de un hueco con modo ofrece nombre, icono, «Guardar en Mis modos» y «Quitar del hueco» (antes «Vaciar», cuyo aviso decía que la plantilla seguía disponible aunque el modo fuera propio). Se pide confirmación solo si se pierde algo.
- Las plantillas y Mis modos solo aparecen en un hueco libre.

## [0.1.0] · 2026-11-02 · Confirmación luminosa de modos

### Añadido
- Al entrar, cambiar o salir de un modo con Ctrl+Shift+1/2/3, la tecla física confirma la pulsación con luz durante aproximadamente 450 ms, incluso con iluminación Apagada.
- Después del aviso se restaura la preferencia de iluminación. En «Al pulsar» se conserva el efecto normal del teclado.
- Escrituras USB serializadas y cancelación del aviso al ajustar la luz, preparar el teclado o salir de la aplicación. Sin sondeo ni escrituras periódicas.

## [0.0.11] · 2026-11-02 · Pastillas de rueda

### Cambiado
- Pastillas independientes de una línea para cada giro, separadas por un icono de rueda.
- Sin lápices bajo los controles ni lista de atajos predefinidos; se graban pulsando cada control.
- Opciones de velocidad, recetas y OBS accesibles desde la propia grabación.

## [0.0.10] · 2026-11-02 · Acabado visual unificado

### Cambiado
- Etiquetas del Docker en Cascadia Code cursiva y gris suave en Directo, Inteligente y Modos.
- Menús y controles con pesos y tonos más suaves; la herencia se indica mediante subrayado punteado.
- Captura de la interfaz actualizada en el README.

## [0.0.9] · 2026-11-02 · Volumen y selección de modos

### Corregido
- Volumen general con pulsación multimedia nativa para el indicador de Windows y ajuste final exacto de ±1, ±2, ±3 o ±5.
- Spotify vuelve a controlar solo su sesión de audio; se recuperan las configuraciones guardadas con su nombre.

### Cambiado
- Los iconos laterales seleccionan el hueco; el «+» superior abre sus opciones o plantillas.

## [0.0.82] · 2026-11-02 · Reposo y eficiencia

### Cambiado
- El indicador nativo de volumen y modos espera eventos: deja de sondear cada 40 ms incluso después de ocultarse.
- La ventana deja de programar consultas de estado al minimizarse o pasar a la bandeja y se actualiza al volver.
- Una sola consulta de estado en curso y sin repintado si la respuesta no cambia.
- Se conserva la interfaz y el motor de acciones de 0.0.81.

## [0.0.81] · 2026-11-02 · Posición inicial

### Cambiado
- Al abrir, la ventana aparece en la esquina inferior derecha del área útil, sobre la barra de tareas (12 px de margen). Después se puede arrastrar.

### Añadido
- Bocetos del logotipo en `docs/` (`3D.jpg`, `ASD.jpg`, `Desmontado.jpg`).

## [0.0.8] · 2026-11-02 · Logotipo lateral y ajustes en la rueda dentada

### Añadido
- Lateral izquierdo con el logotipo definitivo a toda la altura: título «REVIENDOCKER» en vector, girado, y el dibujo del interruptor. Original en `docs/LOGO_DEFINITIVO_LATERAL.jpg`.
- Rueda dentada de **ajustes** abajo a la derecha, tras la ×. Despliega en vertical teclado, motor y enchufe, solo con iconos. Lleva un punto propio únicamente si el teclado o el motor no están bien; se cierra al pulsar fuera, con Esc o tras buscar el teclado.

### Cambiado
- La barra superior desaparece. Minimizar, cerrar y ajustes pasan a una franja discreta abajo a la derecha; la ventana se arrastra desde cualquier zona no interactiva.
- Menús y editor se centran sobre el área de contenido y terminan sobre la franja inferior.
- La ventana se arrastra desde cualquier zona no interactiva, no solo desde el lateral y la franja.
- Iluminación: solo la bombilla, mismo tamaño y aspecto que el ▶ de la izquierda (se quita el icono de paleta).
- Captura del `README` actualizada.

### Eliminado
- Los tres iconos de estado de la izquierda de la barra de título y el título centrado.

## [0.0.7] · 2026-11-02 · Reorganización del repositorio

Sin cambios visibles ni de funcionamiento en la app.

### Cambiado
- Raíz limpia: `src/` (motor, servidor y ventana), `web/` (interfaz y assets), `docs/` (guía de uso), `tools/` (compilación e iconos) y `tests/`. Los ficheros se movieron con `git mv`, así que conservan su historial.
- La compilación del `.exe` pasa a `tools/build_exe.ps1`; se ejecuta igual desde cualquier carpeta.
- Descripción y etiquetas del repositorio en GitHub actualizadas; captura de la ventana en el `README`.

### Eliminado
- `assets/icon.svg`, que ya no se usaba.

## [0.0.6] · 2026-11-02 · Ventana fija y menús compactos

### Añadido
- `PRODUCT.md`: fuente única de producto y estilo (paleta, estados, tipografía, esquinas, movimiento). Sustituye a `DISEÑO.md`.
- `CHANGELOG.md` y `version.py`; el nombre de la versión aparece en la bandeja.
- Botón ▶ a la izquierda del selector de Modos: activa el modo seleccionado ahora (o vuelve a Directo).

### Cambiado
- Ventana de tamaño fijo, 720 × 420: no se redimensiona ni se maximiza (sin botón, sin bordes de arrastre, sin Win+Flecha). La app corrige el tamaño real al abrir.
- Espacios verticales recortados; el carril izquierdo y la botonera ✓/× quedan a la misma distancia del docker; los botones de la barra de título se alinean con esas columnas.
- La tecla de activación de Inteligente (una sola, común a todo el modo) sale del menú «Atajos para» y pasa a tres botones rotulados Shift, Ctrl y Alt en el carril izquierdo.
- «Añadir una app» y las plantillas de Modos usan chips con icono y nombre, como «Atajos para». Las plantillas solo se abren desde el menú de cada hueco; un hueco vacío salta directo a ellas. «Nuevo modo» pide nombre y un icono entre 16 en una sola fila.
- Menús superpuestos anclados arriba (no saltan al crecer la vista previa) y editor de tecla compacto, sin subtítulos largos.
- Estados: ✓ verde (relleno con cambios pendientes) y × roja; selección con borde blanco y halo; entrada de capas con fundido corto.

### Eliminado
- Panel «Modos de trabajo» del ajuste izquierdo, selector de tecla dentro de «Atajos para», redimensionado y maximizado de ventana.

## [0.0.5] · 2026-11-02 · Estructura común y Modos con Ctrl+Shift

### Cambiado
- Modos se cambian con **Ctrl+Shift+1/2/3** (antes Alt+Shift); repetirlo vuelve a Directo.
- Menús de Directo, Inteligente y Modos como capa superpuesta sobre el docker, sin empujarlo.
- Misma estructura en los tres modos: barra superior, iconos + docker + iconos, mensaje centrado. En Directo e Inteligente el carril reserva tres marcadores.
- «Modo en blanco» pasa a ser la plantilla «Nuevo modo», con nombre e icono a elegir; el icono de cualquier modo se cambia desde su menú.
- Aviso nativo del modo activo abajo a la derecha, sobre la bandeja.
- Mini docker solo en la vista previa de las plantillas.

## [0.0.4] · 2026-11-01 / 02 · Interfaz compacta

### Añadido
- Perfiles de Directo (guardar y cargar asignaciones confirmadas, nombres de hasta 12 caracteres).
- Menú de cada modo con edición y borrado integrados.

### Cambiado
- Cabecera reorganizada: tres iconos de estado a la izquierda, logotipo centrado.
- Editor de tecla superpuesto y unificado en los tres modos; ajustes de OBS agrupados.
- «Atajos para» compacto, con un icono por app; mensaje contextual bajo la botonera; ventana más compacta.

## [0.0.3] · 2026-11-01 · Modos, volumen y motor

### Añadido
- Modo **Modos**: tres huecos con plantillas y cambio rápido con Alt+Shift+1/2/3, grabación directa en el visor y edición con el lápiz bajo cada pieza.
- Luz del teclado con los tres modos reales, con envío en vivo.
- Puente de volumen con aviso nativo; instancia única por mutex y HTTP (sin iconos duplicados en la bandeja).
- «Aplicar cambios» y «Descartar» (✓ / ×), con aviso cuando el teclado necesita preparación.
- Pestañas «Atajos para» por app con detección de la app real y «Crear atajos para…».

### Cambiado
- Escritura USB corregida al formato real del CH57x (`0x8890`), con errores visibles.
- Una columna central con el selector de modo sobre el teclado; secciones plegables.
- Nitidez visual: manifiesto PerMonitorV2, ClearType y geometría precisa.

## [0.0.2] · 2026-10-31 · Identidad visual

### Cambiado
- Icono nuevo (R · v · D), título vectorial con degradado metálico en Doris PP, interfaz en Expressway y esquinas suaves.
- Cabecera con logotipo actualizado e iconos renovados con fondo transparente.
- Primera release publicada en GitHub con `RevienDocker.exe`.

## [0.0.1] · 2026-10-31 · Primera versión

### Añadido
- Aplicación de escritorio para Windows: `RevienDocker.exe` con ventana propia sin marco, bandeja, instancia única y USB por hidapi.
- Modos Directo e Inteligente, capas por app, tecla de activación, acciones de OBS por WebSocket y persistencia.
- Editor de botón con captura de teclado (1 a 3 teclas), ratón completo, recetas de rueda y velocidad, botón Probar y modo simulador.
- Ventana redimensionable por bordes y esquinas.
