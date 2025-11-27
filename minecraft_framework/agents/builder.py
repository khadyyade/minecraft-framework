"""
BuilderBot skeleton.

Responsabilidades:
- Recibir `map.v1` de ExplorerBot y generar un plan / BOM.
- Publicar `materials.requirements.v1` hacia MinerBot.
- Recibir `inventory.v1` y, cuando haya materiales suficientes, ejecutar la construcción
  (simulada) publicando `build.v1` con progreso.

Muchos pasos están indicados como TODO para que los alumnos implementen los detalles.
"""
import asyncio
from multiprocessing import Queue
from typing import Dict, Any

from minecraft_framework.core import BaseAgent, AgentState
from minecraft_framework.messages import MaterialsRequirementsV1, BuildV1


class BuilderBot(BaseAgent):
    def __init__(self, name: str, in_queue: Queue, q_explorer: Queue, q_miner: Queue, q_builder: Queue, mc=None):
        super().__init__(name, in_queue, q_explorer, q_miner, q_builder)
        self.current_plan = None
        self.bom = {}
        self.inventory = {}
        self.mc = mc  # Minecraft connection (opcional)

    async def _run_task(self):
        # Bucle principal: espera map.v1, genera BOM, espera materiales y construye
        self.estadoActual("Builder started and waiting for map.v1 messages")
        while not self._stop_requested:
            incoming = await self.leerMensaje()
            if incoming:
                if isinstance(incoming, dict) and incoming.get("type") == "map.v1":
                    payload = incoming.get("payload", {})
                    await self._handle_map(payload)
                elif isinstance(incoming, dict) and incoming.get("type") == "inventory.v1":
                    payload = incoming.get("payload", {})
                    await self._handle_inventory(payload)
                elif isinstance(incoming, dict) and incoming.get("type") == "control":
                    self.gestionarControles(incoming.get("payload", {}))
                else:
                    self.estadoActual(f"Builder got unknown message: {incoming}")

            await asyncio.sleep(0.3)

    async def _handle_map(self, payload: Dict[str, Any]):
        # Recibe mapa de ExplorerBot, genera plan de construcción y publica BOM
        # TODO: analizar heights y flat_zones para generar plan
        self.estadoActual("Received map.v1; generating simple plan and BOM (simulated)")
        # Plan simple de ejemplo: construir 10x10 de stone
        self.current_plan = {"template": "simple_square", "params": {"w": 10, "d": 10}}
        self.bom = {"stone": 100}
        msg = MaterialsRequirementsV1(bom=self.bom).to_message(origin=self.name)
        self.enviarMensaje("MinerBot", msg)
        self.estadoActual(f"Published materials.requirements.v1 with BOM: {self.bom}")

    async def _handle_inventory(self, payload: Dict[str, Any]):
        # Recibe actualización de inventario de MinerBot e inicia construcción si hay suficientes materiales
        inv = payload.get("inventory", {})
        complete = payload.get("complete", False)
        self.inventory.update(inv)
        self.estadoActual(f"Inventory update: {self.inventory}; complete={complete}")
        # comprobar si tenemos suficientes materiales
        if all(self.inventory.get(k, 0) >= v for k, v in self.bom.items()):
            await self._start_build()

    async def _start_build(self):
        # Ejecuta la construcción: obtiene posición del jugador, coloca bloques y publica progreso
        self.estadoActual("Starting build. Placing blocks...")
        total_steps = 10
        
        # Si tenemos conexión real, obtener posición del jugador como base
        base_x, base_y, base_z = 0, 64, 0
        if self.mc is not None:
            try:
                pos = self.mc.player.getTilePos()
                base_x, base_y, base_z = pos.x + 5, pos.y, pos.z
                self.mc.postToChat(f"BuilderBot: Iniciando construcción en ({base_x}, {base_y}, {base_z})")
            except Exception as e:
                self.estadoActual(f"Error getting player position: {e}")
        
        for i in range(total_steps):
            if self.state == AgentState.PAUSED:
                await asyncio.sleep(0.5)
                continue
            
            # Colocar bloque real si tenemos conexión
            if self.mc is not None:
                try:
                    # Construir una línea de bloques como demo
                    import sys
                    import os
                    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                    mcpi_path = os.path.join(base, "AdventuresInMinecraft-PC", "MyAdventures")
                    if mcpi_path not in sys.path:
                        sys.path.insert(0, mcpi_path)
                    import mcpi.block as block
                    self.mc.setBlock(base_x + i, base_y, base_z, block.STONE.id)
                    self.estadoActual(f"Placed block at ({base_x + i}, {base_y}, {base_z})")
                except Exception as e:
                    self.estadoActual(f"Error placing block: {e}")
            
            progress = (i + 1) / total_steps
            details = {"step": i + 1, "total": total_steps, "pos": (base_x + i, base_y, base_z)}
            msg = BuildV1(progress=progress, details=details).to_message(origin=self.name)
            # broadcast build progress to all known agents
            for target in self.out_queues.keys():
                self.enviarMensaje(target, msg)
            self.estadoActual(f"Published build.v1 progress={progress:.2f}")
            await asyncio.sleep(1)
        
        if self.mc is not None:
            self.mc.postToChat("BuilderBot: Construcción completada!")
        self.estadoActual("Build completed")


def agent_process_main(in_queue: Queue, q_explorer: Queue, q_miner: Queue, q_builder: Queue, **kwargs):
    """Entry point para ejecutar en un proceso separado.

    Args:
        in_queue: Cola de entrada del agente
        q_explorer: Cola del ExplorerBot
        q_miner: Cola del MinerBot
        q_builder: Cola del BuilderBot
        **kwargs: Parámetros adicionales (mc_host, mc_port)
    """
    # Intentar conectar a Minecraft si se proporcionan credenciales
    mc = None
    mc_host = kwargs.get("mc_host")
    mc_port = kwargs.get("mc_port")
    
    if mc_host and mc_port:
        try:
            import sys
            import os
            base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            mcpi_path = os.path.join(base, "AdventuresInMinecraft-PC", "MyAdventures")
            if os.path.exists(mcpi_path):
                sys.path.insert(0, mcpi_path)
            from mcpi.minecraft import Minecraft
            mc = Minecraft.create(mc_host, mc_port)
            print(f"[BuilderBot] Connected to Minecraft at {mc_host}:{mc_port}")
        except Exception as e:
            print(f"[BuilderBot] Could not connect to Minecraft: {e}. Using simulation.")
    
    bot = BuilderBot("BuilderBot", in_queue, q_explorer, q_miner, q_builder, mc=mc)
    try:
        import asyncio
        asyncio.run(bot.iniciarAgente())
    except KeyboardInterrupt:
        bot.estadoActual("KeyboardInterrupt in process")
