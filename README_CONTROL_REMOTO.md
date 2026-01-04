# Control Remoto - Resumen Rápido

## Archivos Creados

1. **remote_control.py** - Servidor de control remoto (Pyro4)
2. **remote_client.py** - Cliente interactivo
3. **GUIA_CONTROL_REMOTO.md** - Guía completa de uso
4. **DOCUMENTACION_CONTROL_REMOTO.txt** - Documentación técnica detallada
5. **ejemplo_integracion_remoto.py** - Código de ejemplo para integración

## Instalación Rápida

```bash
pip install Pyro4
```

## Uso Básico

### 1. Habilitar en el Servidor

Editar `main.py` y añadir antes del `try:`:

```python
from remote_control import start_remote_server
import threading

remote_thread = threading.Thread(
    target=start_remote_server,
    args=(q_explorer, q_miner, q_builder),
    kwargs={"host": "0.0.0.0", "port": 9090},
    daemon=True
)
remote_thread.start()
```

### 2. Ejecutar el Servidor

```bash
python main.py
```

### 3. Conectar el Cliente

En la misma máquina (o otra en la red):

```bash
python remote_client.py
```

Se conecta automáticamente a `localhost:9090`.

### 4. Comandos Disponibles

```
explorer start [x] [z] [range]
miner start [x] [z] [y] [strategy]
miner fulfill
builder plan [template]
builder bom
builder build
pause [agent]
resume [agent]
stop [agent]
status [agent]
workflow [params...]
```

## Ejemplo de Sesión

```
> explorer start
✓ Comando 'start' enviado a ExplorerBot

> builder plan torre.csv
✓ Comando 'plan' enviado a BuilderBot

> miner fulfill
✓ Comando 'fulfill' enviado a MinerBot

> builder build
✓ Comando 'build' enviado a BuilderBot
```

## ⚠️ Importante

- Solo usar en redes locales de confianza
- Sin autenticación implementada
- No exponer a Internet

## Documentación Completa

Ver **GUIA_CONTROL_REMOTO.md** para instrucciones detalladas y **DOCUMENTACION_CONTROL_REMOTO.txt** para explicación técnica.

