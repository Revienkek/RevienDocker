# Volumen · 0.0.9

> Documento histórico. Para el funcionamiento y diagnóstico actuales, consulta [Volumen y rueda](VOLUMEN_Y_RUEDA.md).

## Volumen general

`adjust_system_volume` envía una pulsación multimedia estándar para activar el indicador de Windows, espera su procesamiento (máximo 150 ms) y fija el valor absoluto solicitado mediante Core Audio. Ya no solicita el indicador propio de Tk para el volumen general.

Prueba con el dispositivo de audio real: desde 50, los pasos ±1, ±2, ±3 y ±5 acabaron exactamente en 51/49, 52/48, 53/47 y 55/45 tras esperar 300 ms. Se restauró el nivel original. El usuario no estaba mirando durante la prueba: la aparición visual del OSD sigue pendiente de confirmación del usuario.

## Spotify

La acción `app_volume` ajusta solo las sesiones de Spotify, incluido el silencio. La plantilla Spotify utiliza esta acción y se migran automáticamente las capas de spotify.exe y los modos guardados con nombre Spotify que aún tenían volumen multimedia general. No se modifica el volumen maestro ni se emite la tecla de volumen del sistema desde esta ruta.

Pruebas controladas: paso exacto de sesión, exclusión de otras sesiones, ausencia de llamadas al volumen maestro y migración de configuración. No había sesión Spotify activa durante la comprobación real; abre Spotify y reproduce audio antes de comprobarlo con el gadget.

## Modos

Los tres iconos laterales seleccionan el hueco. El «+» superior abre su menú; un hueco vacío abre las plantillas. La activación del motor se conserva mediante Ctrl+Shift+1/2/3.
