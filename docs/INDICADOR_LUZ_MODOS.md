# Indicador físico de modo: investigación para 0.1.0

Estado: resuelto para la confirmación **breve** solicitada en 0.1.0.
Revien aclaró que el objetivo es avisar al entrar/salir, no reservar una luz
permanentemente. La interpretación inicial que figura abajo quedó descartada.

## Solución validada e implementada

Con iluminación Apagada, Revien pulsó la tecla 1. Después se activó Al pulsar
por USB, sin otra pulsación: confirmó que se encendió la luz 1. El firmware
recuerda la última tecla física incluso con las luces apagadas.

El motor aprovecha ese recuerdo inmediatamente después de Ctrl+Shift+1/2/3:
activa Al pulsar y restaura la preferencia al cabo de 450 ms. En Al pulsar no
necesita escribir: el teclado ya confirma la pulsación. No se simulan teclas
ni se modifican asignaciones. No se promete un color o brillo concreto.

`src/mode_light.py` cancela temporizadores antiguos para que no sobrescriban un
nuevo aviso o un ajuste manual. Comparte el cerrojo USB con las escrituras de
configuración. Salir restaura la preferencia si hay un aviso pendiente. No hay
sondeo ni refresco continuo. Si otra tecla se pulsa durante el breve aviso,
Al pulsar puede seguir esa tecla: no se trata de un LED reservado.

La activación desde la interfaz no enciende una tecla física porque no permite
elegir cuál recuerda el firmware. La reconexión no reproduce avisos antiguos.

## Interpretación inicial (sustituida)

Mientras esté activo un modo 1, 2 o 3, mantener iluminada su tecla física,
independientemente de las pulsaciones posteriores y de la preferencia de luz
del usuario. Al salir del modo, restaurar esa preferencia. No sustituir este
indicador por un efecto en la interfaz ni por la última tecla pulsada.

## Prueba física con Revien (2026-11-02)

Dispositivo conectado: VID 1189, PID 8890. Aplicación cerrada y preferencia
guardada `led_mode: 0` (Apagada).

1. Se aplicó temporalmente el comando conocido de iluminación 1 (Al pulsar).
2. Revien pulsó y soltó la tecla 1: indicó que la luz 1 estaba encendida.
3. Pulsó y soltó la tecla 2: confirmó que la luz cambió a la 2.
4. Se restauró el modo 0 (Apagada); el envío USB terminó correctamente.

Por tanto, habilitar Al pulsar al activar un modo no mantiene su indicador:
la siguiente tecla usada lo desplaza. Esta prueba no demuestra que el firmware
carezca de otras órdenes; demuestra que el mecanismo conocido no basta.

## Vías contrastadas

- `src/app.py`, `CH57xController.led_messages`: secuencia global de 64 bytes
  `03 A1 01`, `03 B0 18 <modo>`, `03 AA A1`. No contiene selector de tecla.
- El controlador externo del mismo PID utiliza esa misma secuencia y un solo
  argumento de modo:
  [ch57x-keyboard-tool, k8890.rs](https://github.com/kriomant/ch57x-keyboard-tool/blob/master/src/keyboard/k8890.rs).
- Se leyeron los descriptores HID del aparato: las interfaces de teclado 0 y 2
  anuncian informes Output de indicadores estándar Num/Caps/Scroll Lock.
  Esto no acredita una correspondencia con las luces de las tres teclas.
  El envío del estado de bloqueo actual, sin alterarlo, devolvió -1 mediante
  hidapi y error 1 mediante `HidD_SetOutputReport` en ambas interfaces.
  No se consiguió control de luz por esta vía.

No se cambiaron asignaciones, firmware ni configuración guardada. No se enviaron
valores de iluminación desconocidos ni barridos de comandos.

## Límite del control permanente (fuera del objetivo aclarado)

Encontrar una orden validada para el PID 8890 que seleccione y mantenga una luz
individual (por documentación del firmware o una captura de software que lo
haga). Después integrar ese control en activación, cambio y salida de modo,
restauración al cerrar y reconexión, sin escrituras periódicas en EEPROM.

La aceptación física requiere que, con luz Apagada, activar el modo 1 ilumine
solo la tecla 1, usar 2/3 y la rueda conserve la 1, cambiar al modo 2 ilumine la
2 y desactivarlo restaure Apagada. Repetir con las demás preferencias de luz.
