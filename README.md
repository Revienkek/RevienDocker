# RevienDocker

Programa de escritorio para Windows que configura el macropad de 3 teclas y 1 rueda (chip WCH CH57x) desde tu PC.

**Versión 0.1.1** · [Descargar `RevienDocker.exe`](https://github.com/Revienkek/RevienDocker/releases/latest) · [Historial de cambios](CHANGELOG.md) · [Producto y estilo](PRODUCT.md) · [Guía de uso](docs/GUIA_USUARIO.md)

![RevienDocker](docs/captura.png)

## Qué necesitas

- Windows 10 u 11.
- El macropad conectado por USB. Sin él, el programa funciona en modo simulador para probar la interfaz.
- RevienDocker debe estar abierto o en la bandeja para que el motor procese los controles.

## Cómo empezar

1. Conecta el macropad por USB y abre **RevienDocker**.
2. En los ajustes, pulsa el enchufe para detectar el teclado.
3. Elige **Directo**, **Inteligente** o **Modos**. Pulsa una tecla o un sentido de la rueda en pantalla y después la tecla que quieras asignarle.
4. Pulsa **Aplicar** para guardar los cambios en el macropad.

Para usar **Inteligente** y **Modos**, deja RevienDocker abierto o minimízalo a la bandeja. Así podrá reconocer la aplicación activa y los cambios de modo.

## Formas de uso

- **Directo:** configura qué hace cada botón y cada giro de la rueda. La asignación vale en cualquier aplicación: por ejemplo, 1 escribe una letra, 2 hace una combinación de teclas y la rueda controla el volumen. Guarda perfiles para cambiar rápidamente entre distintas configuraciones.
- **Inteligente:** los mismos controles pueden hacer cosas distintas según la aplicación que estés usando. Configura, por ejemplo, copiar y pegar en el trabajo, controles de OBS al emitir y acciones multimedia en otra app. Elige un modificador para cada aplicación: al mantenerlo, los botones usan sus acciones alternativas; sin él, conservan las acciones normales de Directo.
- **Modos:** guarda hasta tres configuraciones para cambiar de tarea sin abrir RevienDocker. Pulsa **Ctrl+Shift+1**, **2** o **3** en el macropad para activar el modo correspondiente; repite la combinación para volver al uso anterior. Por ejemplo, activa Música para controlar Spotify mientras trabajas y vuelve después a tus asignaciones habituales. Empieza con una plantilla o crea un modo desde cero.

En los tres casos puedes asignar acciones de teclado, multimedia o ratón. Cada sentido de la rueda se configura por separado; también puede controlar el volumen general o el de Spotify sin cambiar el otro.

## Ventana

- La ventana tiene tamaño fijo: no se redimensiona ni se maximiza. Al abrirse aparece en la esquina inferior derecha, sobre la barra de tareas.
- Abajo a la derecha están minimizar, cerrar y los ajustes (rueda dentada: estado del teclado y del motor, y buscar el teclado). No hay barra de título: la ventana se mueve arrastrando cualquier zona que no sea un botón o un campo.

## Estructura del repositorio

```
src/     motor, servidor local y ventana de escritorio (Python)
web/     interfaz (index.html, studio.css, studio.js, iconos) y sus assets
docs/    guía de uso
tools/   compilación del .exe y generación de iconos
tests/   pruebas automáticas
```

## Guía completa

La guía paso a paso (modo Inteligente, capas por app, OBS, recetas de rueda y problemas conocidos) está en [docs/GUIA_USUARIO.md](docs/GUIA_USUARIO.md). El producto y el estilo oficial están en [PRODUCT.md](PRODUCT.md).

## Compilar el ejecutable

Solo si quieres generar tu propio `.exe`:

```bash
pip install -r requirements.txt -r requirements-dev.txt
powershell -ExecutionPolicy Bypass -File tools\build_exe.ps1
```

El resultado queda en `dist\RevienDocker.exe`.

Para ejecutarlo desde el código sin compilar:

```bash
pip install -r requirements.txt
python src/studio_app.py
```

## Datos y privacidad

- Con el `.exe`, tu configuración se guarda en `%APPDATA%\RevienDocker\studio.json`. Desde el código, en `studio.json` en la raíz del repositorio.
- El programa solo escucha en tu propio PC (`127.0.0.1`). Otras webs no pueden usarlo para pulsar teclas.

## Pruebas

```bash
python -m unittest discover -s tests -t . -v
```

Las pruebas no necesitan el teclado ni OBS.

## Estado

La configuración de teclado y la grabación de atajos están probadas con simulador y pruebas automáticas. El formato de escritura USB es el de ch57x-keyboard-tool para este chip. Los botones de ratón atrás/adelante y los modos de luz 0–3 no están confirmados en el teclado real.

## Licencia

Licencia MIT, ver [LICENSE](LICENSE). Los iconos de interfaz son de Lucide (licencia ISC).
