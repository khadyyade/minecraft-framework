# Cambios Implementados - BaseAgent y Registro Dinámico

## ✅ Cambios realizados

### 1. Renombrado de `core.py` → `baseAgent.py`
- Archivo movido de `minecraft_framework/core.py` a `minecraft_framework/baseAgent.py`
- Todas las referencias actualizadas en:
  - `explorer.py`
  - `miner.py`
  - `builder.py`
  - `__init__.py`

### 2. Ciclo Percepción-Decisión-Acción implementado

Se añadieron tres métodos abstractos a `BaseAgent`:

```python
async def perceive(self) -> Dict[str, Any]:
    """Fase de PERCEPCIÓN: lee mensajes y estado del entorno"""
    raise NotImplementedError("Subclasses must implement perceive()")

async def decide(self, perception: Dict[str, Any]) -> Dict[str, Any]:
    """Fase de DECISIÓN: procesa percepción y determina acción"""
    raise NotImplementedError("Subclasses must implement decide()")

async def act(self, decision: Dict[str, Any]):
    """Fase de ACCIÓN: ejecuta la decisión"""
    raise NotImplementedError("Subclasses must implement act()")
```

El método `_run_task()` ahora implementa este ciclo automáticamente:

```python
async def _run_task(self):
    while not self._stop_requested:
        perception = await self.perceive()
        decision = await self.decide(perception)
        await self.act(decision)
        await asyncio.sleep(0.1)
```

### 3. Sistema de Registro Dinámico (`registry.py`)

Nuevo módulo que descubre agentes automáticamente usando **reflexión**:

**Características:**
- ✅ Escanea `agents/` y carga todos los archivos `.py`
- ✅ Verifica que las clases hereden de `BaseAgent` (sin import directo)
- ✅ Valida que tengan los métodos requeridos: `perceive`, `decide`, `act`, `iniciarAgente`
- ✅ Soporta también descubrimiento de estrategias en `strategies/`
- ✅ Singleton global con `get_registry()`

**Uso:**
```python
from minecraft_framework.registry import get_registry

registry = get_registry()
print(registry.list_agents())  # ['ExplorerBot', 'MinerBot', 'BuilderBot']

# Obtener una clase dinámicamente
ExplorerBot = registry.get_agent("ExplorerBot")
```

### 4. Ejemplo de uso: `example_registry.py`

Script de demostración que muestra:
- Cómo obtener el registro
- Listar agentes y estrategias descubiertos
- Obtener una clase de agente dinámicamente
- Inspeccionar métodos disponibles

**Ejecutar:**
```powershell
python minecraft-framework/example_registry.py
```

## 📋 Qué falta por hacer (TODOs para Persona 1)

### En `baseAgent.py`:

1. **Checkpointing** - Guardar/cargar estado del agente:
```python
def save_checkpoint(self, filepath: str):
    # TODO: Serializar estado a JSON
    pass

def load_checkpoint(self, filepath: str):
    # TODO: Deserializar y restaurar estado
    pass
```

2. **Logging estructurado** - Escribir logs en archivo además de consola:
```python
def estadoActual(self, msg: str, level: str = "INFO"):
    # TODO: Además de print, escribir en logs/agent_name.log
    pass
```

3. **Validación de transiciones de estado** - En `gestionarControles()`:
```python
# TODO: Validar que STOPPED no pueda ir a RUNNING directamente
# TODO: Enviar acknowledgment (ACK) al emisor del comando
```

4. **Validación de mensajes**:
```python
def validate_message(self, message: Dict[str, Any]) -> bool:
    # TODO: Verificar estructura (type, origin, timestamp, payload)
    pass
```

### En `explorer.py`, `miner.py`, `builder.py`:

Cada agente debe **refactorizar** su código actual para usar el ciclo perceive-decide-act:

**Ejemplo para ExplorerBot:**

```python
async def perceive(self) -> Dict[str, Any]:
    # Leer mensajes de control
    incoming = await self.leerMensaje()
    return {
        "incoming_message": incoming,
        "current_position": (self.x, self.z),
        "state": self.state
    }

async def decide(self, perception: Dict[str, Any]) -> Dict[str, Any]:
    # Decidir si escanear, pausar, o procesar comando
    if perception["state"] == AgentState.PAUSED:
        return {"action": "wait"}
    
    if perception["incoming_message"]:
        msg = perception["incoming_message"]
        if msg.get("type") == "control":
            return {"action": "handle_control", "payload": msg}
    
    return {"action": "scan_terrain"}

async def act(self, decision: Dict[str, Any]):
    action = decision.get("action")
    
    if action == "wait":
        await asyncio.sleep(0.5)
    elif action == "handle_control":
        self.gestionarControles(decision["payload"])
    elif action == "scan_terrain":
        heights = self._simulate_scan(self.x, self.z, self.scan_range)
        flat_zones = self._detect_flat_zones(heights)
        map_msg = MapV1(...).to_message(origin=self.name)
        self.enviarMensaje("BuilderBot", map_msg)
```

### Tests unitarios:

Crear `tests/test_baseAgent.py`:
```python
def test_perceive_decide_act_cycle():
    # TODO: Verificar que el ciclo funciona correctamente
    pass

def test_dynamic_registration():
    # TODO: Verificar que registry descubre agentes
    pass
```

## 🔍 Verificar que funciona

1. **Probar registro dinámico:**
```powershell
python minecraft-framework/example_registry.py
```

Deberías ver:
```
Agentes registrados:
  • ExplorerBot
  • MinerBot
  • BuilderBot
```

2. **Verificar imports:**
```powershell
python -c "from minecraft_framework.baseAgent import BaseAgent; print('OK')"
```

3. **Verificar que los agentes heredan correctamente:**
```powershell
python -c "from minecraft_framework.agents.explorer import ExplorerBot; print(hasattr(ExplorerBot, 'perceive'))"
```

## 📚 Documentación actualizada

- `README.md` - Añadida sección de Arquitectura con ciclo perceive-decide-act
- `__init__.py` - Actualizado para exportar `baseAgent` y `registry`

## ⚠️ Importante

Los agentes **aún no implementan** `perceive()`, `decide()`, `act()` - tendrás que refactorizarlos.

Actualmente usan el método antiguo `_run_task()` que está sobreescrito. Para migrarlos:

1. Extraer lógica de `_run_task()` actual
2. Dividirla en las 3 fases: percepción, decisión, acción
3. Implementar los 3 métodos abstractos
4. Borrar el `_run_task()` antiguo (usará el de BaseAgent)
