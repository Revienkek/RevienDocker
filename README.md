# RevienDocker

Programa de escritorio para Windows que configura el macropad de 3 teclas y 1 rueda (chip WCH CH57x) desde tu PC.

![Icono de RevienDocker](assets/icon.png)

## Qué necesitas

- Windows 10 u 11.
- El macropad conectado por USB. Sin él, el programa funciona en modo simulador para probar la interfaz.
- RevienDocker debe estar abierto o en la bandeja para que el motor procese los controles.

## Cómo empezar

1. Abre **RevienDocker** (el acceso directo del escritorio o `dist\RevienDocker.exe`).
2. Pulsa el enchufe de la cabecera para buscar el teclado. La píldora «Simulador» pasa a verde cuando lo detecta.
3. Elige un botón en el teclado (panel 1) y decide qué hace en el panel 2.
4. Pulsa **Aplicar cambios**. Eso escribe la configuración dentro del teclado.

El teclado se prepara para comunicarse con el motor de RevienDocker, que ejecuta las acciones configuradas.

## Formas de uso

- **Directo:** asignaciones que se usan en cualquier aplicación; puedes guardarlas como perfiles.
- **Inteligente:** cada botón cambia según la app que tengas en primer plano (por ejemplo, otro atajo en OBS que en el navegador). Necesita RevienDocker en marcha; cerrar la ventana la oculta en la bandeja y el motor sigue activo.

- **Modos:** hasta tres configuraciones independientes. Se activan con **Ctrl+Shift+1/2/3** (repetirlo vuelve a Directo). Los menús de Directo, Inteligente y Modos se despliegan encima del docker. A la izquierda del docker, un icono por hueco: pulsa uno para ver su menú (nombre, plantilla, vaciar); el «+» de un hueco vacío abre su menú para elegir plantilla.

Selecciona la sección en la cabecera. El lápiz de cada control abre sus ajustes.

## Ventana

- Arrastra cualquier borde o esquina para cambiar el tamaño (mínimo 720 × 560).
- Los botones de la esquina superior derecha minimizan, maximizan o cierran.

## Guía completa

La guía paso a paso (modo Inteligente, capas por app, OBS, recetas de rueda y problemas conocidos) está en [GUIA_USUARIO.md](GUIA_USUARIO.md). El diseño visual está en [DISEÑO.md](DISEÑO.md).

## Compilar el ejecutable

Solo si quieres generar tu propio `.exe`:

```bash
pip install -r requirements.txt -r requirements-dev.txt
powershell -ExecutionPolicy Bypass -File build_exe.ps1
```

El resultado queda en `dist\RevienDocker.exe`.

Para ejecutarlo desde el código sin compilar:

```bash
pip install -r requirements.txt
python studio_app.py
```

## Datos y privacidad

- Con el `.exe`, tu configuración se guarda en `%APPDATA%\RevienDocker\studio.json`. Desde el código, en `studio.json` junto a los archivos.
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
