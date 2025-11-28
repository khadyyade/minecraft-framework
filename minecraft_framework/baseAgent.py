# Hemos creado una clase padre BaseAgent que cada agente extiende
# Tiene varias funciones ya implementadas como
# - enviarMensaje
# - gestionarControles
# - leerMensaje
# - iniciarAgente
# También tenemos los metodos abstractos para cada agente
# - 
# Gestionamos la comunicación entre los procesos con multiprocessing.Queue

import asyncio
from enum import Enum
from multiprocessing import Queue
from typing import Dict, Any, Optional
import time
import json



################
# PATRÓN STATE #
################

class EstadoAgente(Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    WAITING = "WAITING"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


###################
# PATRÓN STRATEGY #
###################

class FaseEstado(Enum):
    PERCEIVING = "PERCEIVING"
    DECIDING = "DECIDING"
    ACTING = "ACTING"
    IDLE = "IDLE"


class BaseAgent:

    # Constructor
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

        # Estado del agente (State Pattern)
        self.estadoActual = EstadoAgente.IDLE
        self.ultimoCambioEstado = time.time()
        self.solicitudParada = False
        
        # Fase del ciclo perceive-decide-act (Strategy Pattern)
        self.faseActual = FaseEstado.IDLE
        
        # Contexto compartido entre fases
        self.context = {
            "perception": None,
            "decision": None,
            "cycle_count": 0
        }

    ############################
    # Métodos ya implementados #
    ############################

    # Imprime un mensaje con timestamp, nombre del agente y estado actual
    def logs(self, msg: str):
        # Parsear la fecha
        fecha = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        # Printear la fecha, el estado, el nombre y un mensaje que recibimos por param
        print(f"[{fecha}] [{self.name}] [{self.estadoActual.value}] {msg}")


    # Busca la cola del agente destino y envía el mensaje en JSON
    def enviarMensaje(self, target: str, message: Dict[str, Any]):
        q = self.out_queues.get(target)
        # Controlar que el destinatario exista
        if q is None:
            self.logs(f"Warning: out_queue for '{target}' not found. Message dropped.")
            return
        # Intentamos transformar a JSON 
        try:
            q.put_nowait(json.dumps(message))
        except Exception:
            q.put_nowait(message)

    # Cambia el estado del agente y registra la transición con timestamp
    def cambiarEstadoAgente(self, nuevoEstado: EstadoAgente, razon: str = ""):
        estadoAnterior = self.estadoActual
        self.estadoActual = nuevoEstado
        self.ultimoCambioEstado = time.time()
        self.logs(f"Pasamos del estado {estadoAnterior.value} a {nuevoEstado.value}. {razon}")

    # Procesa los comandos de control (pause, resume, stop, update) y cambia el estado del agente
    def gestionarControles(self, control: Dict[str, Any]):
        # Dentro de control, que es un diccionario (clave valor) tenemos algo así: {"nuevoEstado": "pause", "args": {}}
        nuevoEstado = control.get("nuevoEstado")
        if nuevoEstado == "pause":
            if self.estadoActual == EstadoAgente.RUNNING:
                self.cambiarEstadoAgente(EstadoAgente.PAUSED, razon="paused by control")
        elif nuevoEstado == "resume":
            if self.estadoActual == EstadoAgente.PAUSED:
                self.cambiarEstadoAgente(EstadoAgente.RUNNING, razon="resumed by control")
        elif nuevoEstado == "stop":
            self.logs("Stop requested")
            self.solicitudParada = True
            self.cambiarEstadoAgente(EstadoAgente.STOPPED, razon="stopped by control")
        elif nuevoEstado == "update":
            self.logs(f"Received update: {control.get('args')}")
            # self.cambiarEstadoAgente(EstadoAgente., razon="stopped by control")
        else:
            self.logs(f"Unknown control command: {nuevoEstado}")

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
        
        self.cambiarEstadoAgente(EstadoAgente.RUNNING, razon="Iniciando bucle principal ")
        try:
            await self._run_task()
        except Exception as e:
            self.logs(f"Unhandled error in run: {e}")
            self.cambiarEstadoAgente(EstadoAgente.ERROR, razon=str(e))


    ############################
    ###### Bucle Principal #####
    ############################

    # Gestionamos el estado () y la estartegia 
    
    async def _run_task(self):
        """
        Bucle principal
        
        Usa State Pattern para gestionar los estados del agente
        Usa Strategy Pattern para las fases
        
        Estados posibles:
            RUNNING     Ejecuta el ciclo perceive-decide-act
            PAUSED      Espera sin ejecutar el ciclo
            WAITING     Espera por condiciones externas
            STOPPED     Termina el bucle
            ERROR       Manejo de errores
        
        Fases del ciclo (cuando state == RUNNING)
            PERCEIVING   perceive(): Obtener información del entorno
            DECIDING     decide(): Procesar y tomar decisiones
            ACTING       act(): Ejecutar acciones
        """
        
        self.logs("Iniciando bucle principal")
        
        while not self.solicitudParada:
            
            # ┌─────────────────────────────────────────────────────────┐
            # │ STATE PATTERN: Gestión de estados del agente           │
            # └─────────────────────────────────────────────────────────┘
            
            if self.estadoActual == EstadoAgente.RUNNING:
                # ESTADO RUNNING: Ejecutar ciclo perceive-decide-act
                await self.ejecutarEstrategias()
                
            elif self.estadoActual == EstadoAgente.PAUSED:
                # ESTADO PAUSED: Esperar sin hacer nada
                self.faseActual = FaseEstado.IDLE
                await asyncio.sleep(0.5)
                
            elif self.estadoActual == EstadoAgente.WAITING:
                # ESTADO WAITING: Esperar condiciones externas
                self.faseActual = FaseEstado.IDLE
                await asyncio.sleep(0.2)
                # Leer mensajes por si llega un comando
                msg = await self.leerMensaje()
                if msg and isinstance(msg, dict) and "nuevoEstado" in msg:
                    self.gestionarControles(msg)
                    
            elif self.estadoActual == EstadoAgente.STOPPED:
                # ESTADO STOPPED: Terminar bucle
                self.logs("Agent stopped")
                break
                
            elif self.estadoActual == EstadoAgente.ERROR:
                # ESTADO ERROR: Esperar recuperación
                self.faseActual = FaseEstado.IDLE
                await asyncio.sleep(1.0)
                
            else:
                # Otros estados
                await asyncio.sleep(0.1)
        
        self.logs("Bucle principal terminado")
    
    
    async def ejecutarEstrategias(self):
        """Ejecuta un ciclo completo perceive-decide-act usando Strategy Pattern.
        
        Este método implementa el ciclo en 3 fases:
            PERCEIVING → Recopilar información
            DECIDING   → Procesar y decidir
            ACTING     → Ejecutar acciones
        """
        
        try:
            # ┌─────────────────────────────────────────────────────────┐
            # │ FASE 1: PERCEIVING                                      │
            # │ Obtener información del entorno y mensajes              │
            # └─────────────────────────────────────────────────────────┘
            
            self.faseActual = FaseEstado.PERCEIVING
            perception = await self.perceive()
            self.context["perception"] = perception
            
            # Si el agente fue pausado durante perceive, salir
            if self.estadoActual != EstadoAgente.RUNNING:
                return
            
            # ┌─────────────────────────────────────────────────────────┐
            # │ FASE 2: DECIDING                                        │
            # │ Procesar percepción y tomar decisiones                  │
            # └─────────────────────────────────────────────────────────┘
            
            self.faseActual = FaseEstado.DECIDING
            decision = await self.decide(perception)
            self.context["decision"] = decision
            
            # Si el agente fue pausado durante decide, salir
            if self.estadoActual != EstadoAgente.RUNNING:
                return
            
            # ┌─────────────────────────────────────────────────────────┐
            # │ FASE 3: ACTING                                          │
            # │ Ejecutar la acción decidida                             │
            # └─────────────────────────────────────────────────────────┘
            
            self.faseActual = FaseEstado.ACTING
            await self.act(decision)
            
            # Incrementar contador de ciclos
            self.context["cycle_count"] += 1
            
            # Pequeña pausa entre ciclos para no saturar CPU
            await asyncio.sleep(0.05)
            
        except NotImplementedError as e:
            # El agente hijo no implementó perceive/decide/act
            self.logs(f" {e}")
            self.cambiarEstadoAgente(EstadoAgente.ERROR, razon=str(e))
            
        except Exception as e:
            # Error durante el ciclo
            self.logs(f"Error en ciclo [{self.faseActual.value}]: {e}")
            self.cambiarEstadoAgente(EstadoAgente.ERROR, razon=str(e))
            await asyncio.sleep(1.0)


    # ============================================================================
    # MÉTODOS ABSTRACTOS: Deben ser implementados por subclases
    # ============================================================================


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
