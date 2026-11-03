# Volumen y rueda: funcionamiento y diagnóstico

Estado registrado el 3 de noviembre de 2026, tras la corrección local de 0.1.6.

## Cómo funciona

El macropad preparado envía F16 al girar a la izquierda y F17 a la derecha.
El motor de RevienDocker recibe cada giro y decide qué acción ejecutar según
Directo, Inteligente o el modo activo. La configuración de cada sentido puede
ser distinta. El motor debe estar abierto, también puede estar en la bandeja.

Para el volumen general, `src/studio_engine.py` ejecuta `adjust_system_volume`,
que envía pulsaciones multimedia nativas de Windows mediante `run_media`. Cada
pulsación equivale normalmente a dos puntos de volumen: los ajustes de la
interfaz ±2, ±4, ±6 y ±10 % envían respectivamente 1, 2, 3 y 5 pulsaciones.
Entre pulsaciones de un mismo giro hay 25 ms. La tecla multimedia también
invoca el indicador nativo de Windows. Los porcentajes dependen del tratamiento
del dispositivo de audio por Windows.

Spotify sigue otra ruta: `app_volume` modifica las sesiones de audio de Spotify
sin ajustar el volumen general. Mantener independientes ambas rutas al cambiarlas.

El documento [VOLUMEN_0.0.9.md](VOLUMEN_0.0.9.md) es histórico: describe una
implementación anterior con Core Audio para el volumen general y pasos de
±1/2/3/5. No describe el código actual.

## Incidencia: Aplicar y la dirección de la rueda

Síntoma observado: tras guardar un cambio de velocidad, la rueda a veces subía
cuando se giraba para bajar, o viceversa. Al desconectar y conectar el macropad,
volvía a funcionar. Se observó que el motor recibía algunos eventos del sentido
contrario y que el problema también aparecía temporalmente al asignar al
dispositivo teclas multimedia directas. Esas pruebas no identificaron por sí
solas la causa interna del firmware.

El desencadenante aislado fue pulsar **Aplicar**: la interfaz reescribía todas
las asignaciones físicas incluso si solo había cambiado un porcentaje. Además,
`normalize_studio` recortaba a 600 caracteres la firma de preparación, cuya
longitud en el dispositivo probado era 791. Así se perdía la comparación con la
firma completa al reiniciar.

Corrección en el commit `0fc3e75`: si la firma guardada coincide con `hwSig()`
en `web/studio.js`, Aplicar confirma y guarda la configuración del motor sin
volver a escribir el macropad. Si no hay firma o no coincide, se conserva la
preparación USB. `src/studio_engine.py` conserva hasta 2048 caracteres de firma.
No se fuerza una firma para un dispositivo cuya preparación no se ha comprobado.

La instalación existente tenía la firma antigua truncada. En esa sesión se
recuperó la firma completa solo después de comprobar que su prefijo coincidía
con la firma guardada y que el mismo dispositivo acababa de prepararse.
Para otra instalación sin esa evidencia, preparar el teclado normalmente.

## Cómo comprobarlo si reaparece

1. Verificar en Directo que izquierda tiene volumen abajo y derecha volumen
   arriba; anotar el paso elegido y si sucede también en otros modos.
2. Reconectar el macropad y comprobar giros lentos y rápidos en ambos sentidos.
3. Cambiar el paso desde el editor, probar antes y después de **Aplicar** y
   observar si el fallo aparece en uno de esos momentos.
4. Revisar `S.flashed`, `hwSig()` y la respuesta de `/api/flash`: una firma
   conocida y coincidente debe permitir guardar sin escribir USB de nuevo.
   Si el teclado no está preparado, la escritura sí es necesaria.
5. Si continúa, registrar las direcciones recibidas antes de asumir un fallo
   del audio o del encoder. El sondeo de `last` solo muestra el último evento:
   puede omitir eventos rápidos, por lo que no mide todos los giros.

Validación física de esta corrección: Revien cambió entre 2 % y 4 %, pulsó
Aplicar y confirmó que la rueda respondía bien en ambos sentidos. No se verificó
con esa prueba cada velocidad, modo o dispositivo de audio posible.
