# Guía de Uso - Minecraft Agents Framework

## ✅ Estado actual de la conexión

La conexión al servidor de Minecraft funciona correctamente:
- **Servidor**: localhost:4711 (RaspberryJuice plugin)
- **Prueba exitosa**: Se colocaron bloques y se envió mensaje al chat
- **Posición del jugador detectada**: (-85, 85, 339)

## 🚀 Cómo ejecutar

### 1. Prueba simple de conexión
```powershell
python "minecraft-framework\test_connection.py"
```

Esto:
- Se conecta al servidor
- Envía "¡Hola desde Python!" al chat
- Coloca un bloque de PIEDRA 3 bloques al este
- Coloca un bloque de ORO 3 bloques al oeste
- Muestra la altura del terreno

### 2. Ejecutar el workflow completo de agentes
```powershell
python "minecraft-framework\run_workflow.py"
```

Esto arrancará los 3 agentes:
- **ExplorerBot**: Escanea el terreno alrededor de (0,0) usando `mc.getHeight(x,z)`
- **BuilderBot**: Recibe el mapa y genera un plan de construcción
- **MinerBot**: Simula recolección de materiales
- **BuilderBot**: Construye una línea de 10 bloques de PIEDRA cerca del jugador

**Verás en el juego**:
- Mensaje en el chat: "BuilderBot: Iniciando construcción en..."
- Una línea de 10 bloques de piedra aparecerá cerca de tu posición
- Mensaje final: "BuilderBot: Construcción completada!"

### 3. Modo simulación (sin Minecraft)
```powershell
python "minecraft-framework\run_workflow.py" --no-minecraft
```

Útil para desarrollo sin necesidad del servidor activo.

## 📋 Qué hace cada agente

### ExplorerBot
- Escanea el terreno usando `mc.getHeight(x, z)` en un área de 17x17 (range=8)
- Detecta zonas planas analizando varianza de elevación
- Publica mensajes `map.v1` con:
  - Matriz de alturas
  - Lista de zonas planas detectadas
  - Coordenadas del área escaneada

### BuilderBot
- Recibe `map.v1` de ExplorerBot
- Genera un plan de construcción simple (10x10 de piedra)
- Publica `materials.requirements.v1` con el BOM (Bill of Materials)
- Espera `inventory.v1` de MinerBot
- Cuando tiene materiales suficientes:
  - Obtiene posición del jugador
  - Construye 10 bloques en línea usando `mc.setBlock(x, y, z, STONE)`
  - Publica `build.v1` con progreso

### MinerBot
- Recibe `materials.requirements.v1` de BuilderBot
- Simula recolección de materiales (todavía no usa mc.getBlock/setBlock)
- Publica `inventory.v1` con progreso incremental
- Marca `complete=True` cuando termina

## 🔧 Arquitectura técnica

### Comunicación
- **Multiprocessing.Queue**: Cada agente tiene su cola de entrada
- **Mensajes JSON**: Todos los mensajes se serializan como JSON
- **Sin bloqueos**: Uso de `asyncio` + `run_in_executor` para leer colas

### Estados del FSM
Cada agente puede estar en:
- `IDLE`: Esperando comando
- `RUNNING`: Ejecutando tarea
- `PAUSED`: Pausado (preserva contexto)
- `WAITING`: Bloqueado esperando recursos
- `STOPPED`: Terminado de forma segura
- `ERROR`: Error irrecuperable

### Flujo de mensajes
```
ExplorerBot --[map.v1]--> BuilderBot
BuilderBot --[materials.requirements.v1]--> MinerBot
MinerBot --[inventory.v1]--> BuilderBot
BuilderBot --[build.v1]--> ALL (broadcast)
```

## 📝 Próximos pasos de desarrollo

### Para Persona 1 (ExplorerBot + Core):
1. Mejorar detección de zonas planas en `_detect_flat_zones()`
2. Implementar análisis de varianza real
3. Añadir soporte para comandos desde el chat de Minecraft
4. Implementar checkpointing (guardar estado en JSON)
5. Añadir tests unitarios para análisis de terreno

### Para Persona 2 (MinerBot + BuilderBot):
1. Implementar estrategias de minería real:
   - `vertical`: Usar `mc.getBlock()` y descender capa por capa
   - `grid`: Escanear región cúbica
   - `vein`: Detectar y seguir vetas de materiales
2. Mejorar `BuilderBot._handle_map()` para generar planes más complejos
3. Añadir templates de construcción (casa, torre, puente)
4. Implementar CLI interactiva en `run_workflow.py` (leer stdin y enviar comandos)
5. Añadir persistencia de inventario y logs de construcción

### Integración:
1. Definir esquemas completos en `messages.py` con validación
2. Añadir logging estructurado con timestamps
3. Implementar manejo robusto de errores y reconexión
4. Crear tests de integración end-to-end

## 🎮 Comandos planeados (para implementar)

Los comandos se enviarían mediante la CLI o el chat de Minecraft:

### Comunes
- `/agent help` - Listar todos los comandos
- `/agent status` - Estado de todos los agentes
- `/agent stop` - Detener todos
- `/agent pause` - Pausar todos
- `/agent resume` - Reanudar todos

### ExplorerBot
- `/explorer start x=0 z=0 range=10` - Iniciar exploración
- `/explorer stop` - Detener exploración
- `/explorer set range 15` - Cambiar rango de escaneo
- `/explorer status` - Ver estado actual

### MinerBot
- `/miner start x=0 y=60 z=0` - Iniciar minería
- `/miner set strategy vertical` - Cambiar estrategia
- `/miner fulfill` - Cumplir BOM actual
- `/miner status` - Ver inventario y estado

### BuilderBot
- `/builder plan list` - Listar templates
- `/builder plan set tower height=10` - Seleccionar plan
- `/builder bom` - Ver Bill of Materials
- `/builder build` - Iniciar construcción

### Workflow completo
```
/workflow run x=0 z=0 range=10 template=house miner.strategy=grid
```

Ejecuta todo el flujo coordinado: explorar → planificar → minar → construir

## 🐛 Solución de problemas

### "Connection refused"
- Verifica que el servidor esté corriendo (`Server/start.bat`)
- Confirma que estás conectado como jugador
- Revisa que el puerto sea 4711 en `Server/plugins/RaspberryJuice/config.yml`

### "Import mcpi could not be resolved"
- Es normal (el IDE no encuentra mcpi porque está en otra carpeta)
- El código funciona en runtime porque se añade al `sys.path`

### Los agentes no hacen nada
- Revisa la consola para ver los logs `[AgentName] [STATE] mensaje`
- Verifica que los mensajes se estén intercambiando (aparecen como `[Main] Message from...`)

### Bloques no aparecen en el juego
- Confirma que la conexión se estableció (debe aparecer `Connected to Minecraft at...`)
- Verifica que el jugador esté en modo creativo o tenga permisos
- Asegúrate de estar cerca de las coordenadas donde construye

## 📚 Archivos importantes

- `minecraft_framework/core.py` - BaseAgent, FSM, helpers
- `minecraft_framework/messages.py` - Estructuras de mensajes
- `minecraft_framework/agents/explorer.py` - ExplorerBot
- `minecraft_framework/agents/miner.py` - MinerBot
- `minecraft_framework/agents/builder.py` - BuilderBot
- `minecraft_framework/cli.py` - Parser de comandos (esqueleto)
- `run_workflow.py` - Orquestador principal
- `test_connection.py` - Prueba de conexión rápida
- `TODOs.md` - División de tareas pendientes
