# Historial de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). Versiones `0.0.x`: una por tanda de trabajo.
La versión actual está en `version.py` y en el nombre de la etiqueta de GitHub (`v0.0.x`). Producto y estilo: [PRODUCT.md](PRODUCT.md).

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
