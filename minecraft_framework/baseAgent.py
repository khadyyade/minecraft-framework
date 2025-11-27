# Hemos creado una clase padre BaseAgent que cada agente extiende
# Tiene varias funciones útiles como
# - enviarMensaje
# - gestionarControles
# - leerMensaje
# - iniciarAgente
# Gestionamos la comunicación entre los procesos con multiprocessing.Queue

import asyncio
from enum import Enum
from multiprocessing import Queue
from typing import Dict, Any, Optional
import time
import json


class AgentState(Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    WAITING = "WAITING"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


class BaseAgent:

    # Cosntructor
    def __init__(self, name: str, in_queue: Queue, q_explorer: Queue, q_miner: Queue, q_builder: Queue):
        self.name = name
        self.in_queue = in_queue
        # Guardar referencias a cada cola
        self.q_explorer = q_explorer
        self.q_miner = q_miner
        self.q_builder = q_builder
        # Diccionario de las colas
        self.out_queues = {
            "ExplorerBot": q_explorer,
            "MinerBot": q_miner,
            "BuilderBot": q_builder
        }
        self.state = AgentState.IDLE
        self._last_transition = time.time()
        self._stop_requested = False


    # Métodos

    # Imprime un mensaje con timestamp, nombre del agente y estado actual
    def estadoActual(self, msg: str):
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print(f"[{ts}] [{self.name}] [{self.state.value}] {msg}")


    # Busca la cola del agente destino y envía el mensaje en JSON
    def enviarMensaje(self, target: str, message: Dict[str, Any]):
        q = self.out_queues.get(target)
        if q is None:
            self.estadoActual(f"Warning: out_queue for '{target}' not found. Message dropped.")
            return
        # Intentamos transformar a JSON 
        try:
            q.put_nowait(json.dumps(message))
        except Exception:
            q.put_nowait(message)

    # Cambia el estado del agente y registra la transición con timestamp
    def cambiarEstadoAgente(self, new_state: AgentState, reason: str = ""):
        prev = self.state
        self.state = new_state
        self._last_transition = time.time()
        self.estadoActual(f"State transition {prev.value} -> {new_state.value}. {reason}")

    # Procesa los comandos de control (pause, resume, stop, update) y cambia el estado del agente
    def gestionarControles(self, control: Dict[str, Any]):
        """Manejar mensajes de control: pause, resume, stop, update.

        `control` es un dict con estructura mínima: { 'cmd': 'pause'|'resume'|... , 'args': {...} }
        """
        
        cmd = control.get("cmd")
        if cmd == "pause":
            if self.state == AgentState.RUNNING:
                self.cambiarEstadoAgente(AgentState.PAUSED, reason="paused by control")
        elif cmd == "resume":
            if self.state == AgentState.PAUSED:
                self.cambiarEstadoAgente(AgentState.RUNNING, reason="resumed by control")
        elif cmd == "stop":
            self.estadoActual("Stop requested")
            self._stop_requested = True
            self.cambiarEstadoAgente(AgentState.STOPPED, reason="stopped by control")
        elif cmd == "update":
            # TODO: procesar actualizaciones de parámetros
            self.estadoActual(f"Received update: {control.get('args')}")
        else:
            self.estadoActual(f"Unknown control command: {cmd}")

    # Leer de la cola de entrada sin bloquear el loop asyncio
    async def leerMensaje(self):

        loop = asyncio.get_running_loop()
        try:
            raw = await loop.run_in_executor(None, self.obtenerMensajeNoWait)
        except asyncio.CancelledError:
            raise
        except Exception:
            raw = None
        if raw is None:
            return None
        # Intentar parsear JSON
        try:
            import json

            msg = json.loads(raw)
        except Exception:
            msg = raw
        return msg


    # Intenta obtener un mensaje de la cola sin esperar (non-blocking)
    def obtenerMensajeNoWait(self):
        try:
            return self.in_queue.get_nowait()
        except Exception:
            return None

    # Inicia el agente, cambia a estado RUNNING y ejecuta la tarea principal
    async def iniciarAgente(self):
        
        self.cambiarEstadoAgente(AgentState.RUNNING, reason="Iniciando bucle principal ")
        try:
            await self._run_task()
        except Exception as e:
            self.estadoActual(f"Unhandled error in run: {e}")
            self.cambiarEstadoAgente(AgentState.ERROR, reason=str(e))

    async def _run_task(self):
        """Implementa el ciclo percepción-decisión-acción.
        
        Las subclases pueden sobreescribir esto completamente o usar perceive/decide/act.
        """
        while not self._stop_requested:
            # Ciclo percepción-decisión-acción
            perception = await self.perceive()
            decision = await self.decide(perception)
            await self.act(decision)
            await asyncio.sleep(0.1)  # Evitar busy-wait

    async def perceive(self) -> Dict[str, Any]:
        """Fase de PERCEPCIÓN: lee mensajes entrantes y estado del entorno.
        
        DEBE ser implementado por subclases.
        Retorna un diccionario con la percepción actual (mensajes, estado, etc).
        """
        raise NotImplementedError("Subclasses must implement perceive()")

    async def decide(self, perception: Dict[str, Any]) -> Dict[str, Any]:
        """Fase de DECISIÓN: procesa la percepción y determina qué hacer.
        
        DEBE ser implementado por subclases.
        Args:
            perception: Datos retornados por perceive()
        Retorna un diccionario con la decisión/acción a tomar.
        """
        raise NotImplementedError("Subclasses must implement decide()")

    async def act(self, decision: Dict[str, Any]):
        """Fase de ACCIÓN: ejecuta la decisión tomada.
        
        DEBE ser implementado por subclases.
        Args:
            decision: Datos retornados por decide()
        """
        raise NotImplementedError("Subclasses must implement act()")
