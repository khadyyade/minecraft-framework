"""
ExplorerBot skeleton.

Responsabilidades principales:
- Escanear el terreno usando `getHeight(x, z)` (o simulación si no hay servidor).
- Detectar zonas planas con baja varianza en elevación.
- Publicar `map.v1` periódicamente hacia BuilderBot.
- Aceptar comandos: pause, resume, stop, update (nuevas coordenadas o rango).

TODOs concretos están marcados a lo largo del fichero.
"""
import asyncio
import random
from multiprocessing import Queue
from typing import Dict, Any, List

from minecraft_framework.core import BaseAgent, AgentState
from minecraft_framework.messages import MapV1


class ExplorerBot(BaseAgent):
    def __init__(self, name: str, in_queue: Queue, q_explorer: Queue, q_miner: Queue, q_builder: Queue, x: int = 0, z: int = 0, scan_range: int = 8, mc=None):
        super().__init__(name, in_queue, q_explorer, q_miner, q_builder)
        self.x = x
        self.z = z
        self.scan_range = scan_range
        self.mc = mc  # Minecraft connection (opcional, si None usa simulación)
        self._paused_event = asyncio.Event()
        self._paused_event.set()

    async def _run_task(self):
        """Bucle principal: escanea y publica `map.v1`.

        Actualmente la función `get_height` está simulada. En una integración real,
        usar `mcpi.minecraft.Minecraft.create()` y `mc.getHeight(x,z)`.
        """
        # Ejecuta el ciclo de exploración: escanea terreno, detecta zonas planas y envía map.v1
        self.estadoActual(f"Starting exploration at x={self.x} z={self.z} range={self.scan_range}")
        while not self._stop_requested:
            if self.state == AgentState.PAUSED:
                self.estadoActual("Explorer paused; waiting to resume")
                await asyncio.sleep(0.5)
                continue

            # Escanear área
            heights = self._simulate_scan(self.x, self.z, self.scan_range)

            # Detectar zonas planas (ejemplo simple)
            flat_zones = self._detect_flat_zones(heights)

            map_msg = MapV1(area={"x": self.x, "z": self.z, "range": self.scan_range}, heights=heights, flat_zones=flat_zones).to_message(origin=self.name)

            # Enviar a BuilderBot si existe
            self.enviarMensaje("BuilderBot", map_msg)
            self.estadoActual(f"Published map.v1 with {len(flat_zones)} flat zones")

            # Chequear cola de control cada iteración
            await asyncio.sleep(2)
            incoming = await self.leerMensaje()
            if incoming:
                # Suponemos que los mensajes de control vienen como dicts con 'cmd'
                if isinstance(incoming, dict) and incoming.get("type") == "control":
                    self.gestionarControles(incoming.get("payload", {}))
                else:
                    self.estadoActual(f"Explorer received: {incoming}")

        self.estadoActual("Explorer exiting main loop")

    def _simulate_scan(self, x: int, z: int, r: int) -> List[List[int]]:
        """Escanea una matriz de alturas (range*2+1) x (range*2+1).

        Usa mc.getHeight(x,z) si hay conexión, sino simula.
        """
        # Escanea el terreno y devuelve una matriz con las alturas de cada bloque
        size = r * 2 + 1
        heights = []
        
        for i in range(-r, r + 1):
            row = []
            for j in range(-r, r + 1):
                if self.mc is not None:
                    # Usar API real de Minecraft
                    try:
                        height = self.mc.getHeight(x + i, z + j)
                        row.append(height)
                    except Exception as e:
                        self.estadoActual(f"Error getting height at ({x+i},{z+j}): {e}")
                        row.append(64)  # fallback
                else:
                    # Simulación
                    row.append(64 + random.randint(-2, 3))
            heights.append(row)
        return heights

    def _detect_flat_zones(self, heights: List[List[int]]) -> List[Dict[str, int]]:
        """Detecta zonas planas simples devolviendo rectángulos candidatos.

        TODO: mejorar con análisis de varianza y tamaño mínimo.
        """
        # Analiza la matriz de alturas y devuelve lista de zonas planas encontradas
        flat = []
        size = len(heights)
        # versión simple: si toda la primera fila tiene la misma altura, lo marca
        first_row = heights[0]
        if all(h == first_row[0] for h in first_row):
            flat.append({"x": self.x, "z": self.z, "w": size, "d": 1})
        return flat


def agent_process_main(in_queue: Queue, q_explorer: Queue, q_miner: Queue, q_builder: Queue, **kwargs):
    """Entry point para ejecutar en un proceso separado.

    Args:
        in_queue: Cola de entrada del agente
        q_explorer: Cola del ExplorerBot
        q_miner: Cola del MinerBot
        q_builder: Cola del BuilderBot
        **kwargs: Parámetros adicionales (mc_host, mc_port, x, z, range)
    """
    # Intentar conectar a Minecraft si se proporcionan credenciales
    mc = None
    mc_host = kwargs.get("mc_host")
    mc_port = kwargs.get("mc_port")
    
    if mc_host and mc_port:
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
            print(f"[ExplorerBot] Connected to Minecraft at {mc_host}:{mc_port}")
        except Exception as e:
            print(f"[ExplorerBot] Could not connect to Minecraft: {e}. Using simulation.")
    
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
    try:
        asyncio.run(bot.iniciarAgente())
    except KeyboardInterrupt:
        bot.estadoActual("KeyboardInterrupt in process")
