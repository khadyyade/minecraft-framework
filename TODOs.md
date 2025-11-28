# TODOs y división del trabajo

Este documento propone una división de tareas para que dos personas trabajen en paralelo sobre el proyecto. Los archivos ya incluidos contienen muchos comentarios y TODOs; este fichero organiza el alcance y la prioridad.

Equipo A (Persona 1) - Exploración y Core:

- Implementar y testear `minecraft_framework/core.py` (FSM, logging, control messages).
- Finalizar `minecraft_framework/agents/explorer.py`: completar scanning, manejo de comandos desde chat y checkpointing.
- Añadir tests unitarios para funciones de análisis de terreno (e.g., variance, flatness detection).
- Documentar en `README.md` detalles del protocolo `map.v1`.

Equipo B (Persona 2) - Minería, Construcción y Orquestación:

- Implementar estrategias de `MinerBot` en `minecraft_framework/agents/miner.py` (vertical, grid, vein).
- Completar `BuilderBot` en `minecraft_framework/agents/builder.py`, BOM generation y procesamiento de inventario.
- Implementar el orquestador `main.py` y la CLI en `minecraft_framework/cli.py`.
- Añadir persistencia de checkpoints (JSON/pickle) para recuperación.

Pasos comunes / Integración:

- Definir y estandarizar los esquemas de mensajes (`messages.py`): `map.v1`, `materials.requirements.v1`, `inventory.v1`, `build.v1`.
- Añadir logging estructurado y timestamps para todas las transiciones de estado.
- Preparar `requirements.txt` y entorno virtual.

Prioridad inicial (MVP):

1. Core y mensajería básica + agentes en modo 'simulado' (no requieren un servidor Minecraft real).
2. Explorador que publica `map.v1` con elevaciones simuladas.
3. Builder que genera un BOM simple y publica `materials.requirements.v1`.
4. Miner que responde con `inventory.v1` simulando recolección.
5. Ejecución de workflow completo en un entorno local.

Notas:

- Cada tarea debe llevar un comentario `TODO: <tarea>` en el código cuando no esté implementada.
- Mantener las comunicaciones basadas en `multiprocessing.Queue` para facilitar testing y aislar procesos.
