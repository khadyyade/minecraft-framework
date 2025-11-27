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
    def __init__(self, name: str, in_queue: Queue, out_queues: Dict[str, Queue], x: int = 0, z: int = 0, scan_range: int = 8):
        super().__init__(name, in_queue, out_queues)
        self.x = x
        self.z = z
        self.scan_range = scan_range
        self._paused_event = asyncio.Event()
        self._paused_event.set()

    async def _run_task(self):
        """Bucle principal: escanea y publica `map.v1`.

        Actualmente la función `get_height` está simulada. En una integración real,
        usar `mcpi.minecraft.Minecraft.create()` y `mc.getHeight(x,z)`.
        """
        self.log(f"Starting exploration at x={self.x} z={self.z} range={self.scan_range}")
        while not self._stop_requested:
            if self.state == AgentState.PAUSED:
                self.log("Explorer paused; waiting to resume")
                await asyncio.sleep(0.5)
                continue

            # Escanear área
            heights = self._simulate_scan(self.x, self.z, self.scan_range)

            # Detectar zonas planas (ejemplo simple)
            flat_zones = self._detect_flat_zones(heights)

            map_msg = MapV1(area={"x": self.x, "z": self.z, "range": self.scan_range}, heights=heights, flat_zones=flat_zones).to_message(origin=self.name)

            # Enviar a BuilderBot si existe
            self.send("BuilderBot", map_msg)
            self.log(f"Published map.v1 with {len(flat_zones)} flat zones")

            # Chequear cola de control cada iteración
            await asyncio.sleep(2)
            incoming = await self._check_incoming()
            if incoming:
                # Suponemos que los mensajes de control vienen como dicts con 'cmd'
                if isinstance(incoming, dict) and incoming.get("type") == "control":
                    self.handle_control(incoming.get("payload", {}))
                else:
                    self.log(f"Explorer received: {incoming}")

        self.log("Explorer exiting main loop")

    def _simulate_scan(self, x: int, z: int, r: int) -> List[List[int]]:
        """Simula una matriz de alturas (range*2+1) x (range*2+1).

        En la implementación real usar `mc.getHeight(x+i,z+j)`.
        """
        size = r * 2 + 1
        heights = []
        base = 64
        for i in range(size):
            row = []
            for j in range(size):
                # pequeña variación aleatoria
                row.append(base + random.randint(-2, 3))
            heights.append(row)
        return heights

    def _detect_flat_zones(self, heights: List[List[int]]) -> List[Dict[str, int]]:
        """Detecta zonas planas simples devolviendo rectángulos candidatos.

        TODO: mejorar con análisis de varianza y tamaño mínimo.
        """
        flat = []
        size = len(heights)
        # versión simple: si toda la primera fila tiene la misma altura, lo marca
        first_row = heights[0]
        if all(h == first_row[0] for h in first_row):
            flat.append({"x": self.x, "z": self.z, "w": size, "d": 1})
        return flat


def agent_process_main(in_queue: Queue, out_queues: Dict[str, Queue], **kwargs):
    """Entry point para ejecutar en un proceso separado.

    Se crea un loop asyncio y se ejecuta `ExplorerBot.run()`.
    """
    bot = ExplorerBot("ExplorerBot", in_queue, out_queues, x=kwargs.get("x", 0), z=kwargs.get("z", 0), scan_range=kwargs.get("range", 8))
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        bot.log("KeyboardInterrupt in process")
