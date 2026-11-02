# Volumen para la futura 0.0.9

- El volumen general se ajusta en `adjust_system_volume` mediante `IAudioEndpointVolume` para conservar pasos exactos de 1, 2, 3 o 5 puntos. Esta ruta ya no envía teclas multimedia de volumen; en el equipo del usuario no aparece el indicador nativo de Windows.
- `show_volume` intenta mostrar un indicador propio con Tk. El informe de PyInstaller de la compilación local 0.0.82 indica `missing module named tkinter`; debe verificarse en una compilación funcional antes de depender de él. Este indicador propio no equivale al solicitado de Windows.
- En el código estable 0.0.82, la plantilla de Spotify asigna acciones multimedia genéricas de volumen y el motor no contiene una acción de volumen por sesión. Esto contradice el comportamiento independiente previamente confirmado por el usuario y necesita recuperación.
- Objetivo: indicador nativo de Windows para volumen general sin perder pasos exactos; Spotify debe controlar solo su sesión de audio. No enviar una tecla multimedia adicional sin comprobar sus efectos, ya que podría alterar el volumen dos veces o mostrar un nivel distinto.
- Pendiente: identificar y validar el mecanismo nativo en el Windows real, además de probar ambos controles con el macropad y Spotify. Reservado para la futura 0.0.9; no publicado como versión.
