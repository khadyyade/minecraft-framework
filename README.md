# Minecraft Agents Framework (esqueleto)

Este repositorio contiene un esqueleto para implementar tres agentes que interactúan con Minecraft: ExplorerBot, MinerBot y BuilderBot.

- Carpeta del paquete: `minecraft_framework`
- Objetivo: usar `asyncio` + `multiprocessing.Queue` para comunicar procesos/agents.

## Configuración y conexión al servidor Minecraft

### Prerequisitos
1. **Servidor Minecraft corriendo**: Ejecuta `AdventuresInMinecraft-PC/Server/start.bat` o `StartServer.bat`
2. **Plugin RaspberryJuice instalado**: Ya está en `Server/plugins/RaspberryJuice/`
3. **Puerto configurado**: Por defecto `4711` (ver `Server/plugins/RaspberryJuice/config.yml`)
4. **Jugador conectado**: Conecta al servidor desde Minecraft (localhost)

### Prueba de conexión rápida

Primero, verifica que puedes conectarte al servidor:

```powershell
python "minecraft-framework/test_connection.py"
```

Este script intentará:
- Conectarse a `localhost:4711`
- Enviar un mensaje al chat del juego
- Obtener tu posición
- Colocar bloques de piedra y oro cerca de ti

Si ves mensajes de éxito (✓), la conexión funciona correctamente.

## Uso rápido (demo)

1. Preparar entorno Python (opcional pero recomendado):
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate
   ```

2. Ejecutar el orquestador con conexión a Minecraft:

```powershell
# Conectar a localhost:4711 (por defecto)
python "minecraft-framework/main.py"

# Especificar host/puerto personalizado
python "minecraft-framework/main.py" --host=127.0.0.1 --port=4711

# Ejecutar en modo simulación (sin conexión a Minecraft)
python "minecraft-framework/main.py" --no-minecraft
```

El script arrancará tres procesos (Explorer, Miner, Builder) que:
- **ExplorerBot**: Escaneará el terreno alrededor de (0,0) y publicará mapas
- **BuilderBot**: Generará un plan y BOM basado en el mapa
- **MinerBot**: Simulará la recolección de materiales
- **BuilderBot**: Construirá una línea de bloques cerca del jugador

El proyecto está incompleto a propósito; revisad `minecraft-framework/TODOs.md` para la división del trabajo y los pasos siguientes.

Comandos soportados (esqueleto):

- Comunes: `/agent help`, `/agent status`, `/agent stop`, `/agent pause`, `/agent resume`
- Explorer: `/explorer start x=<int> z=<int> [range=<int>]`, `/explorer stop`, `/explorer set range <int>`, `/explorer status`
- Miner: `/miner start [x=<int> z=<int> y=<int>]`, `/miner set strategy <vertical|grid|vein>`, `/miner fulfill`, `/miner pause`, `/miner resume`, `/miner status`
- Builder: `/builder plan list`, `/builder plan set <template> [params]`, `/builder bom`, `/builder build`, `/builder pause`, `/builder resume`
- Workflow: `/workflow run [x=<int> z=<int>] [range=<int>] [template=<name>] [miner.strategy=...]`

Leed los archivos dentro de `minecraft-framework/minecraft_framework` para más detalles y comentarios.
