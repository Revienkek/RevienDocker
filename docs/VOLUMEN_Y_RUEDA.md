# Volumen y rueda: funcionamiento y diagnóstico

Estado actualizado el 4 de noviembre de 2026; cambio local pendiente de validación física.

## Cómo funciona

El macropad preparado envía F16 al girar a la izquierda y F17 a la derecha.
El motor de RevienDocker recibe cada giro y decide qué acción ejecutar según
Directo, Inteligente o el modo activo. La configuración de cada sentido puede
ser distinta. El motor debe estar abierto, también puede estar en la bandeja.

El volumen general usa dos pulsaciones multimedia nativas de Windows por giro,
normalmente 4 puntos, y conserva el indicador de Windows. Para Spotify y otras
sesiones de audio configuradas, el motor ajusta directamente 4 puntos de la
sesión correspondiente sin cambiar el volumen general. El selector de velocidad
se oculta para el volumen; los valores antiguos de velocidad no modifican el paso.
El icono de volumen junto a la papelera abre el selector de destino para cada
giro en Directo, Inteligente y Modos. Ofrece Windows, Spotify y las aplicaciones
con sesión de audio en el dispositivo de salida predeterminado. Las acciones de volumen de OBS usan un paso fijo de 4 dB.

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

El cambio físico de modo conserva el aviso en pantalla y deja de escribir los
comandos USB del destello. Esta medida requiere validación física al alternar
entre Windows y Spotify sin reconectar. El control por sesión modifica el
mezclador de Windows. La barra interna de Spotify requiere una integración
con el reproductor que todavía está pendiente.
