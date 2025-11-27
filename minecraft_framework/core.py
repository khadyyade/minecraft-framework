"""
Core utilities: Agent base class, FSM states, and queue-based messaging helpers.

Este módulo proporciona una base que debe ser extendida por cada agente.
Se usa `multiprocessing.Queue` para comunicación entre procesos.

Muchos métodos están intencionalmente incompletos y con TODOs para que los
alumnos los completen como parte del proyecto.
"""
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
    """Clase base para todos los agentes.

    - `in_queue` recibe mensajes que otros agentes/envían.
    - `out_queues` es un diccionario {agent_name: Queue} para enviar mensajes.
    """

    def __init__(self, name: str, in_queue: Queue, out_queues: Dict[str, Queue]):
        self.name = name
        self.in_queue = in_queue
        self.out_queues = out_queues
        self.state = AgentState.IDLE
        self._last_transition = time.time()
        self._stop_requested = False

    def log(self, msg: str):
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print(f"[{ts}] [{self.name}] [{self.state.value}] {msg}")

    def send(self, target: str, message: Dict[str, Any]):
        """Enviar un mensaje a otro agente por su queue.

        Si el target no existe, lo registramos y continuamos.
        """
        q = self.out_queues.get(target)
        if q is None:
            self.log(f"Warning: out_queue for '{target}' not found. Message dropped.")
            return
        # Serializamos a JSON para evitar problemas con objetos no serializables
        try:
            q.put_nowait(json.dumps(message))
        except Exception:
            # fallback: intentar sin serializar
            q.put_nowait(message)

    def transition(self, new_state: AgentState, reason: str = ""):
        prev = self.state
        self.state = new_state
        self._last_transition = time.time()
        self.log(f"State transition {prev.value} -> {new_state.value}. {reason}")

    def handle_control(self, control: Dict[str, Any]):
        """Manejar mensajes de control: pause, resume, stop, update.

        `control` es un dict con estructura mínima: { 'cmd': 'pause'|'resume'|... , 'args': {...} }
        """
        cmd = control.get("cmd")
        if cmd == "pause":
            if self.state == AgentState.RUNNING:
                self.transition(AgentState.PAUSED, reason="paused by control")
        elif cmd == "resume":
            if self.state == AgentState.PAUSED:
                self.transition(AgentState.RUNNING, reason="resumed by control")
        elif cmd == "stop":
            self.log("Stop requested")
            self._stop_requested = True
            self.transition(AgentState.STOPPED, reason="stopped by control")
        elif cmd == "update":
            # TODO: procesar actualizaciones de parámetros
            self.log(f"Received update: {control.get('args')}")
        else:
            self.log(f"Unknown control command: {cmd}")

    async def _check_incoming(self):
        """Leer de la cola de entrada sin bloquear el loop asyncio.

        Los mensajes están serializados como JSON por diseño.
        """
        # NOTE: multiprocessing.Queue is not awaitable; usamos run_in_executor
        loop = asyncio.get_running_loop()
        try:
            raw = await loop.run_in_executor(None, self._get_nowait)
        except asyncio.CancelledError:
            raise
        except Exception:
            raw = None
        if raw is None:
            return None
        # intentar parsear JSON
        try:
            import json

            msg = json.loads(raw)
        except Exception:
            msg = raw
        return msg

    def _get_nowait(self):
        try:
            return self.in_queue.get_nowait()
        except Exception:
            return None

    async def run(self):
        """Bucle principal del agente; cada subclase implementa `_run_task`."""
        self.transition(AgentState.RUNNING, reason="starting main loop")
        try:
            await self._run_task()
        except Exception as e:
            self.log(f"Unhandled error in run: {e}")
            self.transition(AgentState.ERROR, reason=str(e))

    async def _run_task(self):
        """Implementado por subclases."""
        raise NotImplementedError()
