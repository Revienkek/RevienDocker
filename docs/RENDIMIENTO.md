# Rendimiento · 0.0.82

Referencia funcional y visual: 0.0.81 (commit 2d286ba).

## Cambios

| Ruta | Antes | Ahora |
|---|---|---|
| Indicador de volumen/modo ya creado | Consulta su cola cada 40 ms, también oculto | Espera bloqueado hasta un aviso; un único temporizador cierra el aviso tras 1,8 s |
| Estado de la ventana oculta/minimizada | Intervalo de JS cada 1,5 s, con comprobación de document.hidden | Sin temporizador de estado; la ventana nativa comunica su visibilidad |
| Estado visible | Solicitudes a intervalo fijo y actualizaciones del DOM | Solicitudes en serie; no se actualiza el DOM si la respuesta es idéntica |

La captura nativa conserva sus consultas de 40 ms solo mientras se graba un atajo. El motor conserva su cola bloqueante y el hook de Windows: no se modifica la selección ni ejecución de acciones, el audio ni el protocolo USB.

## Comprobaciones

- `python -m unittest tests.test_idle -v`: indicador, render del nivel y cierre programado sin sondeo (mock de Tk/Win32).
- `node --check web/studio.js`: sintaxis.
- Comprobación del planificador en Node: ocultar cancela el temporizador, restaurar programa actualización, solo una petición simultánea, respuesta idéntica no repinta.

Las comprobaciones con dobles no sustituyen la prueba del ejecutable con el dispositivo. No se publica una reducción porcentual de CPU o RAM sin una medición comparable. WebView2 conserva un coste fijo de memoria. Se conserva el empaquetado y las dependencias de la versión anterior para evitar cambios de plataforma en esta tanda.

## Medición local en bandeja

Una ejecución de cada .exe con `--minimized`, 4 segundos de arranque y una ventana de medida de 5 segundos, incluyendo los descendientes de cada instancia (8 procesos). Se cerraron solo las instancias de medición.

| Versión | CPU acumulada durante 5 s | Memoria privada agregada | Working set agregado |
|---|---:|---:|---:|
| 0.0.81 | 0,0469 s | 218,4 MiB | 407,4 MiB |
| 0.0.82 | 0 s registrados | 222,7 MiB | 420,2 MiB |

Muestra corta, sin interacción con el gadget. La memoria agregada suma también páginas compartidas en el working set: no equivale a RAM exclusiva. Estos datos respaldan menor actividad en reposo, no una mejora de memoria ni una garantía de CPU cero en cualquier equipo.
