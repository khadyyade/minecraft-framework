# Hemos creado una clase padre BaseAgent que cada agente extiende
# Tiene varias funciones ya implementadas como
# - enviarMensaje
# - gestionarControles
# - leerMensaje
# - iniciarAgente
# También tenemos los metodos abstractos para cada agente
#
# Gestionamos la comunicación entre los procesos con multiprocessing.Queue

import asyncio
from enum import Enum
from multiprocessing import Queue
from typing import Dict, Any, Optional
import time
import json


# Estados del agente

class EstadoAgente(Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    WAITING = "WAITING"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


# Estados de la ejecución del agente cuando está en RUNNING

class FaseEstado(Enum):
    PERCEIVING = "PERCEIVING"
    DECIDING = "DECIDING"
    ACTING = "ACTING"
    IDLE = "IDLE"


class BaseAgent:

    ###############
    # Constructor #
    ###############

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
        
        # Fase del ciclo perceive-decide-act (State Pattern)
        self.faseActual = FaseEstado.IDLE
        
        # variable que tiene el contexto compartido entre fases
        self.context = {
            "perception": None,
            "decision": None,
            "cycle_count": 0
        }
        
        # Task asyncio de lectura de mensajes (para cancelación instantánea)
        self.mensaje_task: Optional[asyncio.Task] = None

    ############################
    # Métodos ya implementados #
    ############################

    # Imprime un mensaje con timestamp, nombre del agente y estado actual
    # Print que vemos en terminal de python: [2025-12-02 11:42:08] [ExplorerBot] [RUNNING] Iniciando bucle principal
    def logs(self, msg: str):
        # Parsear la fecha
        fecha = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        # Printear la fecha, el estado, el nombre y un mensaje que recibimos por param
        print(f"[{fecha}] [{self.name}] [{self.estadoActual.value}] {msg}")


    # Busca la cola del agente destino y envía el mensaje en JSON
    # El mensaje del tercer parametro se debe haber creado usando la clase messages.py
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
    def cambiarEstadoAgente(self, cmd: EstadoAgente, razon: str = ""):
        estadoAnterior = self.estadoActual
        self.estadoActual = cmd
        self.ultimoCambioEstado = time.time()
        self.logs(f"Pasamos del estado {estadoAnterior.value} a {cmd.value}. {razon}")

        # Escribir el estado actual en un archivo para que el workflow pueda leerlo
        try:
            import os
            state_file = f"/tmp/{self.name}_state.txt" if os.name != 'nt' else f"C:\\temp\\{self.name}_state.txt"
            os.makedirs(os.path.dirname(state_file), exist_ok=True)
            with open(state_file, 'w') as f:
                f.write(f"{cmd.value}\n{razon}\n{self.ultimoCambioEstado}")
        except Exception as e:
            pass  # No es crítico si falla

    # Procesa los comandos de control (pause, resume, stop, update) y cambia el estado del agente
    def gestionarControles(self, control: Dict[str, Any]):
        """
        Gestiona comandos de control del agente.

        Este método es principalmente para comandos que llegan a través de perceive(),
        ya que pause/resume/stop son manejados inmediatamente por _leer_mensajes_continuamente().

        Args:
            control: Diccionario con cmd y args. Ejemplo: {"cmd": "pause", "args": {}}
        """
        cmd = control.get("cmd")

        if cmd == "pause":
            # Pausar desde estados RUNNING o WAITING
            if self.estadoActual in (EstadoAgente.RUNNING, EstadoAgente.WAITING):
                self.cambiarEstadoAgente(EstadoAgente.PAUSED, razon="pausado por el usuario")

        elif cmd == "resume":
            # Reanudar solo si estamos pausados
            if self.estadoActual == EstadoAgente.PAUSED:
                self.cambiarEstadoAgente(EstadoAgente.RUNNING, razon="reanudado por el usuario")

        elif cmd == "stop":
            # Detener en cualquier momento - MATAR EL PROCESO
            self.logs("Solicitud de STOP recibida - MATANDO PROCESO")
            self.solicitudParada = True
            self.cambiarEstadoAgente(EstadoAgente.STOPPED, razon="detenido por el usuario")

            # MATAR EL PROCESO INMEDIATAMENTE sin limpieza
            import os
            self.logs("TERMINANDO PROCESO CON os._exit()")
            os._exit(0)  # FUERZA terminación INMEDIATA

        elif cmd == "update":
            # Recibir nuevos parámetros puede reactivar al agente
            self.logs(f"Actualización recibida: {control.get('args')}")
            # Cambiar a RUNNING solo si no estaba ya en RUNNING
            if self.estadoActual != EstadoAgente.RUNNING:
                self.cambiarEstadoAgente(EstadoAgente.RUNNING, razon="se han recibido nuevos parametros")

        elif cmd == "status":
            # El comando status se maneja en perceive() de cada agente específico
            pass

        elif cmd == "help":
            # El comando help se maneja en perceive() de cada agente específico
            pass

        else:
            self.logs(f"Comando desconocido: {cmd}")

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
    
    # Lee mensajes continuamente en paralelo al ciclo principal
    # Esto permite respuesta INSTANTÁNEA a comandos
    async def _leer_mensajes_continuamente(self):
        """
        Lee mensajes de forma reactiva SOLO para comandos de control críticos.

        Procesa INSTANTÁNEAMENTE:
        - pause: Pausa el agente (cambia a PAUSED)
        - resume: Reanuda el agente (cambia a RUNNING si estaba PAUSED)
        - stop: Detiene el agente completamente y termina el proceso
        - help: Muestra ayuda en el chat de Minecraft (delegado a perceive)
        - status: Muestra estado actual del agente (delegado a perceive)

        REENCOLA TODO LO DEMÁS para que perceive() lo procese.
        Esto incluye: update, help, status, mensajes entre agentes (map.v1, materials.requirements.v1, etc)
        """
        while not self.solicitudParada:
            raw = self.obtenerMensajeNoWait()
            if raw is None:
                await asyncio.sleep(0.05)
                continue

            try:
                parsed = json.loads(raw)
            except Exception:
                # No es JSON, reencolar
                try:
                    self.in_queue.put_nowait(raw)
                except Exception:
                    self.in_queue.put(raw)
                await asyncio.sleep(0.05)
                continue

            # Solo procesar comandos de control críticos que requieren respuesta instantánea
            if isinstance(parsed, dict) and parsed.get("type") == "control":
                payload = parsed.get("payload", {})
                cmd = payload.get("cmd")

                # PAUSE: Pausar el agente inmediatamente
                if cmd == "pause":
                    if self.estadoActual == EstadoAgente.RUNNING:
                        self.cambiarEstadoAgente(EstadoAgente.PAUSED, razon="pausado por el usuario")
                    elif self.estadoActual == EstadoAgente.WAITING:
                        self.cambiarEstadoAgente(EstadoAgente.PAUSED, razon="pausado por el usuario")
                    continue  # Ya procesado, NO reencolar

                # RESUME: Reanudar el agente inmediatamente
                elif cmd == "resume":
                    if self.estadoActual == EstadoAgente.PAUSED:
                        self.cambiarEstadoAgente(EstadoAgente.RUNNING, razon="reanudado por el usuario")
                    continue  # Ya procesado, NO reencolar

                # STOP: Detener el agente completamente y MATAR EL PROCESO
                elif cmd == "stop":
                    self.logs("Solicitud de STOP recibida - MATANDO PROCESO INMEDIATAMENTE")
                    self.solicitudParada = True
                    self.cambiarEstadoAgente(EstadoAgente.STOPPED, razon="detenido por el usuario")

                    # MATAR EL PROCESO INMEDIATAMENTE sin limpieza
                    # os._exit() termina el proceso SIN ejecutar cleanup handlers
                    # Es más agresivo que sys.exit() y funciona incluso si hay operaciones bloqueadas
                    import os
                    self.logs("TERMINANDO PROCESO AHORA CON os._exit()")
                    os._exit(0)  # FUERZA terminación INMEDIATA del proceso


            # TODO LO DEMÁS se reencola (update, status, help, mensajes entre agentes)
            try:
                self.in_queue.put_nowait(raw)
            except Exception:
                self.in_queue.put(raw)

            await asyncio.sleep(0.05)

    # Inicia el agente en estado IDLE y ejecuta la tarea principal
    async def iniciarAgente(self):
        
        self.logs("Iniciando bucle principal en estado IDLE")
        try:
            await self._run_task()
        except Exception as e:
            self.logs(f"Ha habido algun error desconocido: {e}")
            self.cambiarEstadoAgente(EstadoAgente.ERROR, razon=str(e))


    ############################
    ###### Bucle Principal #####
    ############################

    # Gestionamos el estado () y la estartegia 
    
    async def _run_task(self):
        """
        Bucle principal CON RESPUESTA INSTANTÁNEA
        
        Usa asyncio.create_task para ejecutar el ciclo y lectura de mensajes en paralelo.
        Esto permite que los comandos se procesen inmediatamente sin esperar a que termine
        el ciclo perceive-decide-act actual.
        
        Usa State Pattern para gestionar los estados del agente
        Usa State Pattern para las fases
        
        Estados posibles:
            IDLE        Esperando comandos sin ejecutar nada
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
        
        self.logs("Tarea generica iniciada con lectura reactiva de mensajes")

        # Iniciar task de lectura de mensajes en paralelo
        self.mensaje_task = asyncio.create_task(self._leer_mensajes_continuamente())
        
        # Bucle "infinito" que solo se detiene si se cambia estado a STOP o si se para todo el programa (CTRL+C)
        
        while not self.solicitudParada:
            
            # Gestión de estados del agente
            
            if self.estadoActual == EstadoAgente.IDLE:
                # ESTADO IDLE: Leer mensajes pero no ejecutar decide/act
                # Esto permite que los comandos cambien el estado a RUNNING
                self.faseActual = FaseEstado.IDLE
                try:
                    # Solo ejecutar perceive para leer mensajes
                    await self.perceive()
                except Exception as e:
                    self.logs(f"Error en perceive (IDLE): {e}")
                await asyncio.sleep(0.1)

            elif self.estadoActual == EstadoAgente.RUNNING:
                # ESTADO RUNNING: Ejecutar ciclo perceive-decide-act continuamente
                # El ciclo se ejecuta mientras el estado sea RUNNING
                try:
                    await self.ejecutarEstrategias()
                except asyncio.CancelledError:
                    self.logs(f"Ciclo cancelado en fase {self.faseActual.value}")
                    # Continuar con el siguiente estado
                except Exception as e:
                    self.logs(f"Error en ciclo RUNNING: {e}")
                    await asyncio.sleep(0.1)

            elif self.estadoActual == EstadoAgente.PAUSED:
                # ESTADO PAUSED: Leer mensajes para poder reactivarse
                # Similar a IDLE, debe poder procesar comandos como "resume" o "update"
                self.faseActual = FaseEstado.IDLE
                try:
                    # Ejecutar perceive para leer mensajes
                    await self.perceive()
                except Exception as e:
                    self.logs(f"Error en perceive (PAUSED): {e}")
                await asyncio.sleep(0.2)

            elif self.estadoActual == EstadoAgente.WAITING:
                # ESTADO WAITING: Esperar condiciones externas pero leer mensajes
                # Debe poder recibir requirements del builder o comandos del usuario
                self.faseActual = FaseEstado.IDLE
                try:
                    # Ejecutar perceive para leer mensajes
                    await self.perceive()
                except Exception as e:
                    self.logs(f"Error en perceive (WAITING): {e}")
                await asyncio.sleep(0.2)
                    
            elif self.estadoActual == EstadoAgente.STOPPED:
                # ESTADO STOPPED: Terminar bucle
                self.logs("Agente parado")
                break
                
            elif self.estadoActual == EstadoAgente.ERROR:
                # ESTADO ERROR: Esperar recuperación
                self.faseActual = FaseEstado.IDLE
                await asyncio.sleep(1.0)
                
            else:
                # Otros estados
                await asyncio.sleep(0.1)
        
        # Cancelar task de mensajes al terminar
        if self.mensaje_task and not self.mensaje_task.done():
            self.mensaje_task.cancel()
            try:
                await self.mensaje_task
            except asyncio.CancelledError:
                pass
        
        self.logs("Bucle principal terminado")
    
    
    async def ejecutarEstrategias(self):

        #Ejecuta un ciclo completo de perceive-decide-act
        
        try:

            # PERCEIVING
            # Obtener información del entorno y mensajes
            
            self.faseActual = FaseEstado.PERCEIVING
            perception = await self.perceive()
            self.context["perception"] = perception
            
            # Si el agente ha sido pausado durante perceive, salir
            if self.estadoActual != EstadoAgente.RUNNING:
                return
            
            # DECIDING
            # Procesar percepción y tomar decisiones
            
            self.faseActual = FaseEstado.DECIDING
            decision = await self.decide(perception)
            self.context["decision"] = decision
            
            # Si el agente ha sido pausado durante decide, salir
            if self.estadoActual != EstadoAgente.RUNNING:
                return
            
            # ACTING
            # Ejecutar la acción decidida
            
            self.faseActual = FaseEstado.ACTING
            await self.act(decision)
            
            # Incrementar contador de ciclos
            self.context["cycle_count"] += 1
            
            # Dar oportunidad a otras tareas asyncio (yield control)
            await asyncio.sleep(0)

        except NotImplementedError as e:
            # El agente hijo no implementó perceive/decide/act
            self.logs(f" {e}")
            self.cambiarEstadoAgente(EstadoAgente.ERROR, razon=str(e))
            
        except Exception as e:
            # Error durante el ciclo
            self.logs(f"Error en ciclo [{self.faseActual.value}]: {e}")
            self.cambiarEstadoAgente(EstadoAgente.ERROR, razon=str(e))
            # Ponemos await para que sea sincrono
            await asyncio.sleep(1.0)


    ######################
    # Métodos abstractos #
    ######################

    # Percive lee mensajes y el estado anterior
    # Genera un diccionaro con todos los datos procesados
    async def perceive(self) -> Dict[str, Any]:
        raise NotImplementedError("El agente debe implementar el método perceive()")

    # Decide recibe el diccionario del estado anterior y toma decisiones
    # Genera un diccionaro con las acciones a realizar
    async def decide(self, perception: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("El agente debe implementar el método decide()")

    # Decide recibe el diccionario de lo que debe hacer
    # Y ejecuta lo necesario
    async def act(self, decision: Dict[str, Any]):
        raise NotImplementedError("El agente debe implementar el método act()")
