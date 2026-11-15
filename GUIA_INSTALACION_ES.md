# Lunar Outpost V3.0 — Guía de instalación (español)

Esta edición incluye **el astronauta pixel art mejorado** (12 poses 96×96) y **Surface Tension.mp3** como música de fondo. La música se reproduce de forma continua con volumen inicial al 28 %; los sonidos de interacción son independientes.

## Qué permanece exactamente igual

- **Centro de operaciones (`hub.png`)**: imagen fija de V2, sin reemplazarla por video.
- **Sala de soporte vital (`life.png`)**: imagen fija de V2, sin reemplazarla por video.
- Generador, escudos e invernadero mantienen los **tres MP4 originales**.
- A.R.I.A. mantiene sus seis retratos.
- Conserva los cuatro sistemas, las herramientas, los minijuegos, los 30 soles y la API NASA DONKI de V2.
- Toda la interfaz del juego está en **inglés**.

## Instalación rápida en una carpeta nueva

1. Descomprime el ZIP y abre `LunarOutpost_V3_Sin_Conflictos` en VS Code.
2. Abre una terminal PowerShell en esa carpeta.
3. Ejecuta:

```powershell
py -m pip install -r requirements-v3.txt
py CHECK_V3.py
py run_v3.py
```

También puedes ejecutar `PLAY_V3_WINDOWS.bat`.

**No uses `py main.py` para V3.** Ese comando inicia V1. Usa **`py run_v3.py`**.

## Controles principales

- **A / D** o flechas: movimiento.
- **Espacio**: salto.
- **E**: interactuar.
- **F**: usar herramienta.
- **Q / R**: cambiar herramienta.
- **TAB**: inventario.
- **H**: pista de A.R.I.A.
- **T**: NASA.
- **N**: avanzar sol desde la base.
- **ESC**: pausa.
- **M**: música de fondo ON/OFF.
- **B**: sonidos de interacción ON/OFF.
- **Pausa → MUSIC VOLUME - / +**: ajustar volumen.

La música empieza en el menú. Se pausa al abrir la pausa general y continúa al reanudar. Sigue sonando al cambiar de salas. Si falla el dispositivo de sonido, el juego intenta continuar sin música.

## Cómo agregar V3 a un repositorio que ya contiene V1 y V2

1. **No copies el ZIP sobre una carpeta donde Git sigue en `Rebasing`.** Ejecuta `git status` primero y termina/soluciona el rebase pendiente.
2. Cuando el repositorio esté limpio, crea una rama:

```powershell
git switch -c lunar-v3-astronaut-music
```

3. Copia a la raíz del repositorio **solo** los nuevos archivos y carpetas del paquete: `lunar_v3/`, `run_v3.py`, `requirements-v3.txt`, `CHECK_V3.py`, `PLAY_V3_WINDOWS.bat`, `PLAY_V3_LINUX.sh`, y la documentación V3. No sobrescribas `main.py`, `game.py`, `settings.py`, `requirements.txt` ni `lunar_v2/`.
4. Prueba `py CHECK_V3.py` y `py run_v3.py`.
5. Confirma y sube:

```powershell
git add lunar_v3 run_v3.py requirements-v3.txt CHECK_V3.py PLAY_V3_WINDOWS.bat PLAY_V3_LINUX.sh
git commit -m "Add Lunar Outpost V3 improved astronaut and music"
git push -u origin lunar-v3-astronaut-music
```

**Nota de derechos de autor:** el MP3 que proporcionaste está integrado en el ZIP local. No lo publiques ni redistribuyas en un repositorio público si no tienes los derechos o licencia correspondientes. Por precaución, el `.gitignore` dentro de `lunar_v3/` lo excluye del commit de Git, pero permanece en tu copia local y funciona al jugar. Si quieres distribuir el juego y no tienes permiso para esa canción, utiliza una banda sonora original o con licencia de redistribución.

## Si falla el audio o la pantalla

- Instala dependencias con `py -m pip ...`, no con `pip` a secas si PowerShell no lo reconoce.
- La música requiere un dispositivo de audio y un decodificador MP3 compatible con tu instalación de Pygame/SDL_mixer.
- Si no se reproduce, el juego debería seguir funcionando, y desde pausa aparecerá `MUSIC UNAVAILABLE`.
- La API NASA usa `DEMO_KEY` de forma predeterminada; para aumentar los límites de uso configura `$env:NASA_API_KEY='TU_CLAVE'` antes de iniciar.
- Usa `py -m unittest discover -s lunar_v3/tests -v` para probar la lógica sin conexión.

## Guardados

V3 escribe en `lunar_v3/user_data/save_v3.json`, sin sobrescribir V1/V2. Si encuentra un guardado antiguo, intenta importarlo solo para lectura. Si el guardado pertenece a otra estructura incompatible, informa del error y puedes empezar nueva partida.
