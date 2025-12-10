# Guía de Comandos del MinerBot

## Integración Completa

El sistema ya está completamente integrado. Aquí está el flujo completo:

```
Chat de Minecraft → main.py (listener) → cli.parse_command() → Queue → Miner.perceive() → Acciones
```

## Cómo Usar el Sistema

### 1. Iniciar el Servidor de Minecraft
```bash
cd Server
./StartServer.sh  # o .bat en Windows
```

### 2. Iniciar el Sistema de Agentes
```bash
python main.py
```

Verás en consola:
```
Iniciando agentes...
Conectando al servidor de Minecraft en: localhost:4711
Todos los agentes se han iniciado. Puedes detener con CTRL+C
Escuchando comandos del chat de Minecraft...
```

### 3. Conectarte al Servidor
- Abre Minecraft
- Ve a "Multijugador"
- Añade servidor con dirección: `localhost`
- Conéctate

### 4. Usar Comandos en el Chat de Minecraft

## Comandos Disponibles del MinerBot

### **Iniciar Minería con Coordenadas Específicas**
```
/miner start x=10 y=64 z=20
```
- Inicia la minería en las coordenadas especificadas
- Si no se especifican coordenadas, usa la posición del jugador
- El MinerBot cambiará a estado `RUNNING`

**Ejemplo sin coordenadas:**
```
/miner start
```

---

### **Cambiar Estrategia de Minería**
```
/miner set strategy vertical
```
**Estrategias disponibles:**
- `vertical` - Mina en columna vertical hacia abajo
- `grid` - Mina en patrón de cuadrícula (TODO: implementar)
- `vein` - Mina siguiendo vetas de recursos (TODO: implementar)

**Ejemplo:**
```
/miner set strategy grid
```

---

### **Modo Fulfill (Cumplir Requisitos)**
```
/miner fulfill
```
- Activa el modo de minería continua
- El MinerBot minará hasta cumplir los requisitos del BuilderBot
- Útil cuando ya tienes requisitos cargados

---

### **Pausar Minería**
```
/miner pause
```
- Pausa temporalmente la minería
- El estado cambia a `PAUSED`
- Se preserva todo el contexto (posición, inventario, estrategia)

---

### **Reanudar Minería**
```
/miner resume
```
- Reanuda la minería desde donde se pausó
- El estado cambia de `PAUSED` a `RUNNING`

---

### **Ver Estado del MinerBot**
```
/miner status
```
**Muestra información detallada:**
- Estado actual (IDLE, RUNNING, PAUSED, STOPPED)
- Estrategia activa
- Inventario de materiales recolectados
- Requisitos pendientes
- Posición actual de minería

**Ejemplo de salida:**
```
State: RUNNING | Strategy: vertical | Inv: 45 items
=== MinerBot Status ===
State: RUNNING
Strategy: vertical
Can Mine: True
Inventory: stone: 12, cobblestone: 24, dirt: 9
Requirements: stone: 50, wood: 20
Position: (10, 64 - depth 12, 20)
```

---

## Comandos Generales (Todos los Agentes)

### **Ayuda**
```
/agent help
```
- Muestra información de ayuda

### **Estado de Todos los Agentes**
```
/agent status
```
- Solicita el estado de todos los agentes activos

### **Pausar Todos**
```
/agent pause
```

### **Reanudar Todos**
```
/agent resume
```

### **Detener Todos**
```
/agent stop
```

---

## Ejemplos de Flujo de Trabajo

### **Ejemplo 1: Minería Simple**
```
/miner start x=0 y=64 z=0
/miner status
# Espera a que mine...
/miner pause
/miner status
/miner resume
```

### **Ejemplo 2: Cambiar Estrategia Durante Minería**
```
/miner start
/miner set strategy vertical
# Mine un poco...
/miner pause
/miner set strategy grid
/miner resume
```

### **Ejemplo 3: Cumplir Requisitos del Builder**
```
# Primero el BuilderBot envía requisitos (automático)
/miner fulfill
/miner status
# El miner minará hasta cumplir los requisitos
```

---

## Seguimiento del Sistema

### **Ver Logs en Consola**
Todos los comandos y acciones se registran en la consola donde ejecutaste `main.py`:

```
[Main] Comando recibido del chat: /miner start x=10 y=64 z=20
[Main] Parseado como: {'type': 'control', 'target': 'MinerBot', 'payload': {...}}
✓ Comando enviado a MinerBot

[2025-12-09 14:30:00] [MinerBot] [IDLE] Starting position updated to: x=10, y=64, z=20
[2025-12-09 14:30:00] [MinerBot] [IDLE] State transition IDLE -> RUNNING. Started mining operation
```

### **Ver Respuestas en el Chat de Minecraft**
El MinerBot responde directamente en el chat:
```
✓ Comando enviado a MinerBot
MinerBot: Starting at (10, 64, 20)
```

---

## Estructura del Sistema

### **Archivo: `cli.py`**
- Contiene `parse_command()` que parsea los comandos del chat
- Convierte comandos en mensajes estructurados JSON

### **Archivo: `main.py`**
- Listener de eventos del chat de Minecraft
- Envía comandos parseados a las colas de los agentes
- Monitorea las colas y muestra mensajes en consola

### **Archivo: `miner.py`**
- **`perceive()`**: Lee mensajes de la cola y procesa comandos
- **`_handle_update()`**: Maneja cambios de estrategia, posición y modo
- **`_report_status()`**: Reporta estado al chat y logs
- **`decide()`**: Decide qué acción tomar basado en percepción
- **`act()`**: Ejecuta la acción de minería

---

## Diagrama de Flujo

```
┌─────────────────────┐
│ Usuario en MC Chat  │
│  /miner start x=10  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  main.py listener   │
│  mc.events.poll()   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  cli.parse_command()│
│  Parsea el comando  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Queue (q_miner)   │
│  Almacena mensaje   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Miner.perceive()   │
│  Lee de la cola     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ _handle_update() /  │
│ _report_status()    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Acción Ejecutada  │
│  + Log + Chat MSG   │
└─────────────────────┘
```

---

## Troubleshooting

### **El comando no hace nada**
- Verifica que el `main.py` esté ejecutándose
- Revisa la consola para ver si el comando fue parseado
- Asegúrate de que la sintaxis del comando sea correcta

### **El MinerBot no responde**
- Verifica que el agente esté en estado `RUNNING` o `IDLE`
- Si está en `PAUSED`, usa `/miner resume`
- Si está en `STOPPED`, reinicia el sistema

### **Error de conexión a Minecraft**
- Verifica que el servidor de Minecraft esté ejecutándose
- Confirma que el puerto sea 4711 (por defecto)
- Revisa que RaspberryJuice esté habilitado en el servidor

---

## Próximos Pasos

1. **Implementar GridMiningStrategy**
2. **Implementar VeinMiningStrategy**
3. **Añadir validación JSON según el esquema de la especificación**
4. **Implementar timestamps ISO 8601**
5. **Añadir contexto de tareas (task_id) en los mensajes**

---

## Notas Técnicas

- Los comandos se convierten en mensajes JSON con estructura:
  ```json
  {
    "type": "control",
    "target": "MinerBot",
    "payload": {
      "cmd": "update",
      "args": {"strategy": "vertical"}
    }
  }
  ```

- El MinerBot valida todos los comandos antes de procesarlos
- Los estados se transicionan de forma atómica con logging
- El inventario se actualiza en tiempo real
- Las coordenadas soportan valores negativos

---

**¡Sistema completamente funcional y listo para usar!** 🎮⛏️

