# Minecraft Agents Framework (esqueleto)

Este repositorio contiene un esqueleto para implementar tres agentes que interactúan con Minecraft: ExplorerBot, MinerBot y BuilderBot.

- Carpeta del paquete: `minecraft_framework`
- Objetivo: usar `asyncio` + `multiprocessing.Queue` para comunicar procesos/agents.

Uso rápido (demo):

1. Preparar entorno Python (ej.: `python -m venv .venv; .\.venv\Scripts\Activate`)
2. Instalar dependencias (si las hay): `pip install -r minecraft-framework/requirements.txt`
3. Ejecutar el orquestador de ejemplo:

```powershell
python "minecraft-framework/run_workflow.py"
```

El proyecto está incompleto a propósito; revisad `minecraft-framework/TODOs.md` para la división del trabajo y los pasos siguientes.

Comandos soportados (esqueleto):

- Comunes: `/agent help`, `/agent status`, `/agent stop`, `/agent pause`, `/agent resume`
- Explorer: `/explorer start x=<int> z=<int> [range=<int>]`, `/explorer stop`, `/explorer set range <int>`, `/explorer status`
- Miner: `/miner start [x=<int> z=<int> y=<int>]`, `/miner set strategy <vertical|grid|vein>`, `/miner fulfill`, `/miner pause`, `/miner resume`, `/miner status`
- Builder: `/builder plan list`, `/builder plan set <template> [params]`, `/builder bom`, `/builder build`, `/builder pause`, `/builder resume`
- Workflow: `/workflow run [x=<int> z=<int>] [range=<int>] [template=<name>] [miner.strategy=...]`

Leed los archivos dentro de `minecraft-framework/minecraft_framework` para más detalles y comentarios.
