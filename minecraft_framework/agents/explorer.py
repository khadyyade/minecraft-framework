"""
ExplorerBot (Punto 4.1)

Requisitos del PDF:

    ExplorerBot surveys the surrounding terrain to identify suitable and stable regions for
construction. Using the getHeight(x, z) function, it scans defined areas and detects
zones with minimal elevation variance that can serve as foundations for BuilderBot’s
structures.
    The user initiates exploration through in-game chat commands, specifying coordinates
and optional range parameters. If new coordinates are received while exploration is active,
ExplorerBot must confirm whether to interrupt the current process or queue the new
request.
    During execution, ExplorerBot periodically publishes map.v1 messages containing
structured terrain data, including elevation maps, identified flat regions, and potential
obstacles. These messages are consumed by BuilderBot to plan construction. The bot
must respond appropriately to control commands (pause, resume, stop) to ensure explo-
ration can be safely suspended, resumed, or terminated while preserving its context.

Resumen de lo que tiene que hacer:
- Escanear el terreno usando getHeight(x, z)
- Detectar zonas planas con pocos desniveles
- Publicar map.v1 periódicamente hacia BuilderBot (Punto 5)
- Aceptar comandos: pause, resume, stop o update con nuevas coordenadas o rango

"""


import asyncio
import random
from multiprocessing import Queue
from typing import Dict, Any, List

from minecraft_framework.baseAgent import BaseAgent, EstadoAgente
from minecraft_framework.messages import MapV1


class ExplorerBot(BaseAgent):
    
    # ============================================================================
    # CONSTRUCTOR
    # ============================================================================
    
    def __init__(self, name: str, in_queue: Queue, q_explorer: Queue, q_miner: Queue, q_builder: Queue, x: int = 0, z: int = 0, scan_range: int = 8, mc=None):
        # Llamamos al constructor padre BaseAgent
        super().__init__(name, in_queue, q_explorer, q_miner, q_builder)
        
        # Parámetros de exploración
        self.x = x
        self.z = z
        self.scan_range = scan_range
        self.mc = mc
        
        # Variables internas
        self.current_heights = None
        self.flat_zones = []
        self.scan_count = 0


    # ============================================================================
    # PATRÓN STRATEGY: metodos perceive-decide-act definidos en baseAgent
    # ============================================================================

    async def perceive(self) -> Dict[str, Any]:
        """🔍 FASE 1: PERCEPCIÓN
        
        Recopila información del entorno:
        - Lee mensajes de control desde la cola (pause, resume, stop, update)
        - Obtiene el estado actual de Minecraft si es necesario
        
        Returns:
            Dict con la percepción actual:
            {
                "messages": [...],           # Mensajes recibidos
                "control_command": {...},    # Comando de control si hay
                "ready_to_scan": bool        # Si está listo para escanear
            }
        """
        perception = {
            "messages": [],
            "control_command": None,
            "ready_to_scan": True
        }
        
        # TODO: Leer mensajes de la cola
        # msg = await self.leerMensaje()
        # if msg:
        #     perception["messages"].append(msg)
        #     if msg.get("type") == "control":
        #         perception["control_command"] = msg.get("payload")
        
        return perception


    async def decide(self, perception: Dict[str, Any]) -> Dict[str, Any]:
        """🤔 FASE 2: DECISIÓN
        
        Procesa la percepción y decide qué hacer:
        - Si hay comando de control, procesarlo
        - Si está listo, decidir escanear el terreno
        - Determinar si hay que actualizar coordenadas
        
        Args:
            perception: Datos de la fase de percepción
            
        Returns:
            Dict con la decisión:
            {
                "action": "scan" | "wait" | "process_control",
                "scan_params": {...},  # Si action == "scan"
                "control": {...}       # Si action == "process_control"
            }
        """
        decision = {
            "action": "wait",
            "scan_params": None,
            "control": None
        }
        
        # TODO: Procesar comandos de control primero
        # if perception["control_command"]:
        #     decision["action"] = "process_control"
        #     decision["control"] = perception["control_command"]
        #     return decision
        
        # TODO: Decidir si escanear
        # if perception["ready_to_scan"]:
        #     decision["action"] = "scan"
        #     decision["scan_params"] = {
        #         "x": self.x,
        #         "z": self.z,
        #         "range": self.scan_range
        #     }
        
        return decision


    async def act(self, decision: Dict[str, Any]):
        """⚡ FASE 3: ACCIÓN
        
        Ejecuta la decisión tomada:
        - Escanea el terreno usando mc.getHeight()
        - Detecta zonas planas
        - Publica mensaje map.v1 a BuilderBot
        - Procesa comandos de control
        
        Args:
            decision: Decisión tomada en la fase anterior
        """
        action = decision.get("action")
        
        if action == "scan":
            # TODO: Escanear el terreno
            # scan_params = decision["scan_params"]
            # heights = await self._scan_terrain(scan_params)
            # self.current_heights = heights
            # 
            # # Detectar zonas planas
            # self.flat_zones = self._detect_flat_zones(heights)
            # 
            # # Publicar map.v1 a BuilderBot
            # map_msg = MapV1(
            #     area={"x": self.x, "z": self.z, "range": self.scan_range},
            #     heights=heights,
            #     flat_zones=self.flat_zones
            # ).to_message(origin=self.name)
            # 
            # self.enviarMensaje("BuilderBot", map_msg)
            # self.estadoActual(f"Published map.v1 with {len(self.flat_zones)} flat zones")
            # self.scan_count += 1
            pass
        
        elif action == "process_control":
            # TODO: Procesar comando de control
            # self.gestionarControles(decision["control"])
            pass
        
        elif action == "wait":
            # Esperar un poco antes del siguiente ciclo
            await asyncio.sleep(0.1)


    # ============================================================================
    # MÉTODOS AUXILIARES
    # ============================================================================

    async def _scan_terrain(self, params: Dict[str, Any]) -> List[List[int]]:
        """Escanea el terreno usando mc.getHeight(x, z).
        
        Args:
            params: {"x": int, "z": int, "range": int}
            
        Returns:
            Matriz de alturas (range*2+1) x (range*2+1)
        """
        # TODO: Implementar escaneo real
        # x, z, r = params["x"], params["z"], params["range"]
        # heights = []
        # 
        # for i in range(-r, r + 1):
        #     row = []
        #     for j in range(-r, r + 1):
        #         try:
        #             height = self.mc.getHeight(x + i, z + j)
        #             row.append(height)
        #         except Exception as e:
        #             self.estadoActual(f"Error getting height at ({x+i},{z+j}): {e}")
        #             row.append(64)  # fallback
        #     heights.append(row)
        # 
        # return heights
        return []


    def _detect_flat_zones(self, heights: List[List[int]]) -> List[Dict[str, int]]:
        """Detecta zonas planas analizando varianza de alturas.
        
        Args:
            heights: Matriz de alturas del terreno
            
        Returns:
            Lista de zonas planas: [{"x": int, "z": int, "w": int, "d": int}, ...]
        """
        # TODO: Implementar detección de zonas planas
        # - Analizar varianza en ventanas deslizantes
        # - Marcar zonas con varianza < umbral como candidatas
        # - Devolver rectángulos que cumplan tamaño mínimo
        
        flat = []
        # size = len(heights)
        # ...
        return flat


# ============================================================================
# ENTRY POINT: Función de proceso
# ============================================================================

def agent_process_main(in_queue: Queue, q_explorer: Queue, q_miner: Queue, q_builder: Queue, **kwargs):
    """Entry point para ejecutar en un proceso separado.

    Args:
        in_queue: Cola de entrada del agente
        q_explorer: Cola del ExplorerBot
        q_miner: Cola del MinerBot
        q_builder: Cola del BuilderBot
        **kwargs: Parámetros adicionales (mc_host, mc_port, x, z, range)
    """
    # Conectar a Minecraft (SIEMPRE requerido, no hay simulación)
    mc = None
    mc_host = kwargs.get("mc_host", "localhost")
    mc_port = kwargs.get("mc_port", 4711)
    
    try:
        import sys
        import os
        # Añadir MyAdventures al path
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        mcpi_path = os.path.join(base, "AdventuresInMinecraft-PC", "MyAdventures")
        if os.path.exists(mcpi_path):
            sys.path.insert(0, mcpi_path)
        from mcpi.minecraft import Minecraft
        mc = Minecraft.create(mc_host, mc_port)
        print(f"[ExplorerBot] ✓ Connected to Minecraft at {mc_host}:{mc_port}")
    except Exception as e:
        print(f"[ExplorerBot] ✗ FATAL: Could not connect to Minecraft: {e}")
        print(f"[ExplorerBot] ✗ ExplorerBot requires a real Minecraft server. Exiting.")
        return
    
    # Crear instancia del agente
    bot = ExplorerBot(
        "ExplorerBot",
        in_queue,
        q_explorer,
        q_miner,
        q_builder,
        x=kwargs.get("x", 0),
        z=kwargs.get("z", 0),
        scan_range=kwargs.get("range", 8),
        mc=mc
    )
    
    # Iniciar el agente (usa el ciclo perceive-decide-act de BaseAgent)
    try:
        asyncio.run(bot.iniciarAgente())
    except KeyboardInterrupt:
        bot.logs("KeyboardInterrupt in process")
